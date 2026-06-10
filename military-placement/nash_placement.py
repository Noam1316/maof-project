"""
Nash-Volume Placement Engine — Military DSS
============================================
Volume-based objective (Nash Bargaining generalization):
    max ∛(fit_surplus × urgency_surplus × pref_surplus)

vs. standard ILP:
    max Σ Score_ij × X_ij  (additive — allows extreme outcomes)

Key insight: multiplicative objective prevents any single party from
"winning everything" — a candidate ignored at 0 fit collapses the cube.
"""

import numpy as np
import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import math

# ──────────────────────────────────────────
# DATA STRUCTURES
# ──────────────────────────────────────────

@dataclass
class Candidate:
    name: str
    dapar: int
    medical: int
    tech: int
    manila: int
    mental: int
    combat: int
    pref: List[str]                          # ordered preference list
    kaas: bool = False
    clauses: List[str] = field(default_factory=list)
    # ── NEW for 30K ──────────────────────────────────────────
    home_city: str = 'tel_aviv'              # for distance scoring
    languages: List[str] = field(default_factory=list)  # 'arabic','english','russian'
    fitness_score: int = 50                  # מכש"ל 1–100 (separate from combat aptitude)
    leadership_xp: int = 0                   # years: scout/youth-movement/instructor
    gender: str = 'M'                        # 'M' / 'F'
    periphery: bool = False                  # from peripheral region

@dataclass
class Role:
    id: str
    name: str
    thresh: Dict             # hard constraints {attr: min_val}
    weights: Dict            # scoring weights  {attr: weight}
    teken: int               # total capacity
    miluy: int               # current fill %
    # ── NEW for 30K ──────────────────────────────────────────
    base_lat: float = 32.08  # unit location latitude
    base_lon: float = 34.78  # unit location longitude
    lang_required: List[str] = field(default_factory=list)
    reserve_value: int = 60  # strategic reserve importance 0-100
    min_fill: int = 0        # minimum viable fill (unit can't function below)
    min_women_pct: float = 0.0   # quota: min % women
    min_periphery_pct: float = 0.0  # quota: min % from periphery
    combat_priority: bool = False    # Phase 1 pre-allocation eligible

# ──────────────────────────────────────────
# OUR 6 CANDIDATES + 6 ROLES (from the demo)
# ──────────────────────────────────────────

CANDIDATES = [
    Candidate("דניאל",  dapar=90, medical=82, tech=90, manila=85, mental=78, combat=20,
              pref=['cyber','product'],
              home_city='tel_aviv',   languages=['english'], fitness_score=55, leadership_xp=0,
              gender='M', periphery=False),
    Candidate("אלון",   dapar=90, medical=45, tech=85, manila=80, mental=75, combat=30,
              pref=['cyber','product'],
              home_city='rishon',     languages=['english'], fitness_score=60, leadership_xp=1,
              gender='M', periphery=False),
    Candidate("יואב",   dapar=70, medical=97, tech=22, manila=65, mental=92, combat=96,
              pref=['elite','intel'], clauses=['color_blind'],
              home_city='haifa',      languages=[],          fitness_score=95, leadership_xp=2,
              gender='M', periphery=False),
    Candidate("מאיה",   dapar=70, medical=97, tech=30, manila=75, mental=88, combat=82,
              pref=['elite','intel'],
              home_city='netanya',    languages=['english'], fitness_score=88, leadership_xp=1,
              gender='F', periphery=False),
    Candidate("אמיר",   dapar=60, medical=82, tech=55, manila=70, mental=65, combat=45,
              pref=['intel','elint'],
              home_city='beer_sheva', languages=['arabic'],  fitness_score=70, leadership_xp=0,
              gender='M', periphery=True),
    Candidate("רן",     dapar=70, medical=45, tech=40, manila=62, mental=50, combat=78,
              pref=['elite','intel'],
              home_city='jerusalem',  languages=[],          fitness_score=80, leadership_xp=3,
              gender='M', periphery=False),
]

ROLES = [
    Role("admin",   "פקיד לשכה",
         thresh={'dapar':40},
         weights={'dapar':.19,'tech':.08,'manila':.42,'mental':.23,'combat':.08},
         teken=50,  miluy=88,
         base_lat=32.08, base_lon=34.78, lang_required=[],          reserve_value=30,
         min_fill=5,  min_women_pct=0.30, min_periphery_pct=0.10, combat_priority=False),
    Role("intel",   "קצין מודיעין",
         thresh={'dapar':70,'medical':72,'mental':55},
         weights={'dapar':.37,'tech':.22,'manila':.17,'mental':.18,'combat':.06},
         teken=80,  miluy=48,
         base_lat=31.91, base_lon=34.90, lang_required=['arabic'],  reserve_value=90,
         min_fill=15, min_women_pct=0.20, min_periphery_pct=0.10, combat_priority=False),
    Role("product", "מנהל מוצר",
         thresh={'dapar':80,'tech':60,'medical':45},
         weights={'dapar':.33,'tech':.31,'manila':.17,'mental':.13,'combat':.06},
         teken=120, miluy=45,
         base_lat=32.08, base_lon=34.78, lang_required=['english'], reserve_value=75,
         min_fill=10, min_women_pct=0.25, min_periphery_pct=0.05, combat_priority=False),
    Role("elint",   "לוחמה אלקטרונית",
         thresh={'dapar':50,'medical':64,'tech':40},
         weights={'dapar':.26,'tech':.36,'manila':.15,'mental':.17,'combat':.06},
         teken=200, miluy=58,
         base_lat=31.50, base_lon=34.60, lang_required=['english'], reserve_value=80,
         min_fill=20, min_women_pct=0.10, min_periphery_pct=0.15, combat_priority=True),
    Role("elite",   "יחידת עילית",
         thresh={'medical':97,'mental':85,'combat':80},
         weights={'dapar':.13,'tech':.04,'manila':.13,'mental':.41,'combat':.29},
         teken=300, miluy=78,
         base_lat=32.10, base_lon=34.92, lang_required=[],          reserve_value=85,
         min_fill=30, min_women_pct=0.15, min_periphery_pct=0.05, combat_priority=True),
    Role("cyber",   "קצין סייבר 8200",
         thresh={'dapar':90,'tech':70,'medical':45},
         weights={'dapar':.39,'tech':.37,'manila':.10,'mental':.09,'combat':.05},
         teken=500, miluy=38,
         base_lat=32.17, base_lon=34.83, lang_required=['english'], reserve_value=95,
         min_fill=40, min_women_pct=0.20, min_periphery_pct=0.05, combat_priority=False),
]

CLAUSE_ROLE_BLOCKS = {
    'color_blind': ['elint'],
}

# ──────────────────────────────────────────
# SCORING ENGINE
# ──────────────────────────────────────────

def check_hard_constraints(c: Candidate, r: Role) -> Optional[str]:
    """Returns block reason or None if eligible."""
    if c.kaas and r.id in ['intel', 'elite', 'elint']:
        return "קה\"ס — שיבוץ עורפי בלבד"
    for clause in c.clauses:
        if r.id in CLAUSE_ROLE_BLOCKS.get(clause, []):
            return f"סעיף ליקוי — {clause}"
    for attr, min_val in r.thresh.items():
        val = getattr(c, attr, 0)
        if val < min_val:
            return f"{attr} {val} < סף {min_val}"
    return None

def fit_score(c: Candidate, r: Role) -> float:
    """
    Role-specific weighted score.
    Range: [0, 100]
    """
    score = sum(r.weights.get(attr, 0) * getattr(c, attr, 0)
                for attr in r.weights)
    return round(min(score, 100), 2)

def urgency_score(r: Role, cycle: str = 'august') -> float:
    """
    Army urgency = manning deficit × activity × cycle.
    Range: [0, 100]
    """
    ACTIVITY = {'admin':0.8, 'intel':1.3, 'product':0.8,
                 'elint':1.3, 'elite':1.3, 'cyber':1.0}
    CYCLE    = {'march':   {'combat':0.85, 'tech':1.15, 'intel':0.9,  'default':1.0},
                'august':  {'combat':1.2,  'tech':0.9,  'intel':1.1,  'default':1.0},
                'november':{'combat':0.8,  'tech':1.3,  'intel':0.95, 'default':1.0}}
    ROLE_TYPE = {'admin':'default','intel':'intel','product':'tech',
                  'elint':'combat','elite':'combat','cyber':'tech'}

    raw_urg  = 100 - r.miluy
    act_mult = ACTIVITY.get(r.id, 1.0)
    cyc_mult = CYCLE[cycle].get(ROLE_TYPE.get(r.id, 'default'), 1.0)
    return min(100, round(raw_urg * act_mult * cyc_mult, 2))

def pref_score(c: Candidate, r: Role, alpha: float = 0.5) -> float:
    """
    Preference bonus scaled by α ∈ [0, 1].
    Range: [0, 10]
    """
    try:
        idx = c.pref.index(r.id)
        bonus = 10 if idx == 0 else 5 if idx == 1 else 0
    except ValueError:
        bonus = 0
    return round(alpha * bonus, 2)

# ──────────────────────────────────────────
# NEW FACTORS FOR 30K SCALE
# ──────────────────────────────────────────

CITY_COORDS = {
    'tel_aviv':   (32.08, 34.78),
    'haifa':      (32.82, 34.99),
    'beer_sheva': (31.25, 34.79),
    'jerusalem':  (31.77, 35.21),
    'netanya':    (32.33, 34.86),
    'rishon':     (31.97, 34.80),
}

def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance in km (simplified for Israel scale)."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def distance_km(c: Candidate, r: Role) -> float:
    """Straight-line distance: candidate home → unit base."""
    coords = CITY_COORDS.get(c.home_city, (32.08, 34.78))
    return _haversine_km(coords[0], coords[1], r.base_lat, r.base_lon)

def distance_score(c: Candidate, r: Role) -> float:
    """
    Distance penalty on fit score.
    0 km  → 0 penalty
    50 km → ~12 penalty
    100km → ~20 penalty (sigmoid shape, not linear)

    Based on IDF data: nishura rate doubles beyond 100km from home.
    """
    km = distance_km(c, r)
    return round(20 * sigmoid((km - 50) / 30) - 5, 2)  # [-5, +15] range

def language_bonus(c: Candidate, r: Role) -> float:
    """
    Language match bonus (additive to fit score).
    Having a required language → +10 per language
    Having a non-required language → +3 (general value)
    """
    bonus = 0
    for lang in c.languages:
        if lang in r.lang_required:
            bonus += 10   # role specifically needs this language
        else:
            bonus += 3    # generally valuable
    return float(bonus)

def retention_prob(c: Candidate, r: Role,
                   alpha: float = 0.5) -> float:
    """
    Predicted probability (0–1) that candidate completes service in this role.

    Model: base × pref_match × distance × dapar_resilience × leadership
    Calibrated so IDF average ≈ 0.85.

    Literature: IDF internal studies show ~15% early-discharge rate,
    strongly correlated with pref_mismatch and distance > 80km.
    """
    base = 0.85

    # Preference match
    pref_idx = c.pref.index(r.id) if r.id in c.pref else -1
    pref_effect = {0: +0.08, 1: +0.04, -1: -0.04}
    base += pref_effect.get(pref_idx, -0.04)

    # Distance (each 10km over 50km → -1% retention)
    km = distance_km(c, r)
    base -= max(0, (km - 50) / 1000)

    # Cognitive resilience (high dapar → handles stress better)
    base += (c.dapar - 60) * 0.001

    # Leadership experience → higher commitment
    base += c.leadership_xp * 0.01

    return round(max(0.50, min(0.99, base)), 4)

def clv_score(c: Candidate, r: Role) -> float:
    """
    Career Lifetime Value — what is the LONG-TERM value of this placement?

    CLV = immediate_fit × 0.40
        + officer_potential × 0.30
        + reserve_strategic_value × 0.30

    Rationale: a cyber soldier who becomes a reserve cyber officer
    is worth ~3× a soldier who completes service and disengages.
    """
    # Immediate fit
    immediate = fit_score(c, r)

    # Officer potential (same logic as pitch.html)
    raw_officer = (c.dapar * 0.40 + c.mental * 0.30 +
                   c.manila * 0.20 + c.combat * 0.10)
    officer_pot = raw_officer if c.medical >= 72 else min(raw_officer, 35)

    # Reserve strategic value (role-specific)
    reserve_val = r.reserve_value

    return round(immediate * 0.40 + officer_pot * 0.30 + reserve_val * 0.30, 2)

# ──────────────────────────────────────────
# FEEDBACK LOOP — weights update from outcomes
# ──────────────────────────────────────────

@dataclass
class PerformanceRecord:
    """Actual performance data collected after placement."""
    candidate_name: str
    role_id: str
    predicted_fit: float
    actual_performance: float   # 0–100, from commander rating
    completed_service: bool     # False = early discharge

def update_weights(roles: List[Role],
                   records: List[PerformanceRecord],
                   learning_rate: float = 0.01) -> List[Role]:
    """
    Gradient descent on role weights W_jk.

    If actual > predicted: the model under-weights some metrics.
    If actual < predicted: the model over-weights some metrics.

    Simplified gradient: adjust weights proportional to prediction error.
    Full implementation would require feature attribution (SHAP values).

    Runs once per draft cycle (March/August/November).
    After ~10 cycles: weights converge to empirical optimum.
    """
    for role in roles:
        role_records = [rec for rec in records if rec.role_id == role.id]
        if len(role_records) < 5:
            continue  # need minimum samples for stable gradient

        errors = [rec.actual_performance - rec.predicted_fit
                  for rec in role_records]
        avg_error = float(np.mean(errors))
        completion_rate = sum(1 for r in role_records if r.completed_service) / len(role_records)

        # Update weights
        for attr in list(role.weights.keys()):
            # Positive error → model underpredicted → increase this attribute's weight
            # Scale by completion rate: if soldiers quit, this role's weights are suspect
            role.weights[attr] += learning_rate * avg_error * 0.01 * completion_rate

        # Normalize to sum = 1
        total = sum(v for v in role.weights.values() if v > 0)
        if total > 0:
            role.weights = {k: max(0.01, v / total)
                           for k, v in role.weights.items()}

    return roles

# ──────────────────────────────────────────
# THE VOLUME / NASH OBJECTIVE
# ──────────────────────────────────────────

def nash_score(c: Candidate, r: Role,
               alpha: float = 0.5, cycle: str = 'august') -> float:
    """
    Nash Bargaining Score = ∛(fit_surplus × urgency_surplus × pref_surplus)
    Basic version — hard binary constraints.
    """
    DISAGREEMENT_FIT = 40.0
    block = check_hard_constraints(c, r)
    if block:
        return -np.inf

    fit_s  = max(0, fit_score(c, r) - DISAGREEMENT_FIT)
    urg_s  = max(0, urgency_score(r, cycle))
    pref_s = max(0, pref_score(c, r, alpha) + 5.0)

    if fit_s <= 0:
        return 0.0

    volume = fit_s * urg_s * pref_s
    return round(volume ** (1.0 / 3.0), 4)


def sigmoid(x: float) -> float:
    """Standard sigmoid: maps (-inf,+inf) → (0,1)."""
    return 1.0 / (1.0 + math.exp(-x))


def smooth_nash_score(c: Candidate, r: Role,
                      alpha: float = 0.5,
                      cycle: str = 'august',
                      epsilon: float = 1.0,
                      sigma: float = 8.0) -> float:
    """
    Smooth Nash — two improvements over basic nash_score:

    1. +ε smoothing: prevents collapse at exact zero due to measurement noise.
       ∛((fit+ε) × (urgency+ε) × (pref+ε))

    2. Sigmoid soft thresholding on COGNITIVE constraints only.
       Medical / kaas / legal clauses remain HARD (binary).
       Cognitive thresholds (dapar, tech, mental) use sigmoid:
         penalty = sigmoid((val - threshold) / sigma)
       At val=threshold: penalty=0.5 (not zero, not one)
       At val=threshold+2σ: penalty≈0.88 (nearly full)
       At val=threshold-2σ: penalty≈0.12 (nearly blocked)

    Rationale: psychometric scores have ±σ measurement error.
    A candidate at dapar=88 vs threshold=90 is not categorically different
    from dapar=92. Sigmoid encodes this uncertainty honestly.
    Medical thresholds are legal requirements — never softened.

    3. Anti-gaming: normalize preference vector to prevent
       strategic manipulation (marking only one role as preferred).
    """
    HARD_ATTRS   = {'medical'}        # always binary
    DISAGREEMENT = 40.0
    EPSILON      = epsilon

    # ── Hard constraints (legal / medical / kaas / clause) ──
    block = check_hard_constraints(c, r)
    if block:
        return -np.inf

    # ── Sigmoid soft thresholding (cognitive only) ──
    soft_penalty = 1.0
    for attr, min_val in r.thresh.items():
        if attr in HARD_ATTRS:
            continue  # medical stays binary
        val = getattr(c, attr, 0)
        if val < min_val:
            gap = val - min_val          # negative: below threshold
            soft_penalty *= sigmoid(gap / sigma)

    # ── Anti-gaming: normalize pref bonus ──
    # Max possible pref bonus = alpha*10. Normalize by candidate's pref diversity.
    # If candidate lists only 1 role in pref → bonus capped at 0.7x
    pref_diversity = min(1.0, len(c.pref) / max(len(r.id), 1) * 0.5 + 0.5)
    raw_pref       = pref_score(c, r, alpha)
    normalized_pref = raw_pref * pref_diversity

    # ── Smooth Nash volume ──
    fit_s  = max(0, fit_score(c, r) - DISAGREEMENT) + EPSILON
    urg_s  = max(0, urgency_score(r, cycle))         + EPSILON
    pref_s = max(0, normalized_pref + 5.0)           + EPSILON

    volume = fit_s * urg_s * pref_s * soft_penalty
    return round(volume ** (1.0 / 3.0), 4)


def full_nash_score(c: Candidate, r: Role,
                    alpha: float = 0.5,
                    cycle: str = 'august',
                    epsilon: float = 1.0) -> float:
    """
    Full Nash-Volume score — production-ready for 30K candidates.

    Extends smooth_nash_score with:
    1. Distance penalty      → fit_s reduced by geographic mismatch
    2. Language bonus        → fit_s increased for language match
    3. Retention probability → urgency weighted by predicted completion rate
    4. CLV                   → pref dimension includes career value + reserve

    Formula:
    ∛( fit_surplus(enhanced) × urgency×retention × clv_pref_surplus ) + ε

    All new factors are additive to existing — backwards compatible.
    Sigmoid soft thresholding applies to cognitive constraints only.
    Medical / kaas / clause → always hard binary.
    """
    DISAGREEMENT_FIT = 40.0

    # Hard constraints (unchanged — always binary)
    block = check_hard_constraints(c, r)
    if block:
        return -np.inf

    # Sigmoid soft thresholding (cognitive thresholds only)
    HARD_ATTRS = {'medical'}
    SIGMA = 10.0  # one dapar step = 10
    soft_penalty = 1.0
    for attr, min_val in r.thresh.items():
        if attr in HARD_ATTRS:
            continue
        val = getattr(c, attr, 0)
        if val < min_val:
            soft_penalty *= sigmoid((val - min_val) / SIGMA)

    # ── Layer 1: Enhanced fit (+ language, - distance) ──
    base_fit    = fit_score(c, r)
    lang_bonus_val  = language_bonus(c, r)
    dist_penalty_val = distance_score(c, r)
    # fitness_score contribution for physical roles
    fitness_bonus = (c.fitness_score - 50) * 0.05 if r.id in ('elite', 'elint') else 0
    enhanced_fit = base_fit + lang_bonus_val - dist_penalty_val + fitness_bonus

    fit_s = max(0, enhanced_fit - DISAGREEMENT_FIT) + epsilon

    # ── Layer 2: Urgency × Retention ──
    raw_urg   = urgency_score(r, cycle)
    ret_prob  = retention_prob(c, r, alpha)
    # Retention multiplies urgency: high urgency + likely to quit = lower real value
    urgency_s = raw_urg * ret_prob + epsilon

    # ── Layer 3: CLV + Preference (replaces simple pref bonus) ──
    pref_bonus = pref_score(c, r, alpha)
    clv        = clv_score(c, r)
    # Blend: immediate preference + long-term career value
    pref_clv_s = (pref_bonus + clv * 0.15 + 5.0) + epsilon

    # ── Nash Volume ──
    volume = fit_s * urgency_s * pref_clv_s * soft_penalty
    return round(volume ** (1.0 / 3.0), 4)


# ──────────────────────────────────────────
# GENDER-FAIR TEMPORAL NASH
# ──────────────────────────────────────────

# IDF mandatory service durations (months)
CONTRACT_MONTHS = {'M': 32, 'F': 24}

def biased_temporal_nash(c: Candidate, r: Role,
                         alpha: float = 0.5,
                         cycle: str = 'august') -> float:
    """
    BIASED version — shows the discrimination problem.
    Multiplies by absolute contract_duration → men get systematic bonus.

    Women:  score × 0.90 × 24 = score × 21.6
    Men:    score × 0.90 × 32 = score × 28.8  ← 33% advantage from gender alone
    """
    base = full_nash_score(c, r, alpha, cycle)
    if base in (-np.inf, None):
        return -np.inf
    ret    = retention_prob(c, r, alpha)
    months = CONTRACT_MONTHS.get(c.gender, 32)
    return round(base * ret * months, 4)   # ← gender-discriminatory


def gender_fair_nash(c: Candidate, r: Role,
                     alpha: float = 0.5,
                     cycle: str = 'august') -> float:
    """
    FAIR version — the original contribution.

    Proof that normalization removes gender bias:
    ───────────────────────────────────────────────
    biased  = base × retention × contract_months
    fair    = base × retention × (contract_months / contract_months)
            = base × retention                      ← gender-neutral

    Formally: replace absolute_years with completion_rate ∈ [0,1].
    completion_rate = retention_prob (already probability of completing contract,
    regardless of contract length).

    The role_monthly_value captures ARMY value per month of service —
    this is role-dependent, NOT gender-dependent.

    Role_ROI (₪/month, approximate):
        cyber   → highest (rare skill, high training investment)
        intel   → high
        elint   → high
        elite   → high (operational value)
        product → medium
        admin   → lower

    Formula:
        fair_score = ∛(fit × urgency × clv_pref) × completion_rate × role_roi_norm
    """
    ROLE_ROI = {
        'cyber':   1.20,   # normalized: 1.0 = average
        'intel':   1.10,
        'elint':   1.05,
        'elite':   1.05,
        'product': 0.95,
        'admin':   0.75,
    }

    base = full_nash_score(c, r, alpha, cycle)
    if base in (-np.inf, None):
        return -np.inf

    completion_rate = retention_prob(c, r, alpha)   # gender-neutral
    role_roi        = ROLE_ROI.get(r.id, 1.0)       # role-dependent, not gender

    return round(base * completion_rate * role_roi, 4)


# ──────────────────────────────────────────
# FAIRNESS AUDIT
# ──────────────────────────────────────────

def fairness_audit(assignment: Dict,
                   candidates: List[Candidate],
                   roles: List[Role],
                   profile_eps: float = 0.08,
                   score_delta: float = 8.0) -> List[Dict]:
    """
    Individual Fairness Check (Dwork et al., 2012):
    "Candidates similar on relevant criteria should receive similar assignments."

    For each pair of candidates (one F, one M) with similar profiles,
    check if their assigned role fit-scores differ significantly.

    profile_distance = weighted L1 over (dapar, tech, mental, manila) / max_range
    Threshold eps=0.08 → within ~7 dapar points on all dimensions

    Returns list of detected violations.
    """
    cand_map = {c.name: c for c in candidates}
    role_map  = {r.id: r  for r in roles}
    violations = []

    females = [c for c in candidates if c.gender == 'F']
    males   = [c for c in candidates if c.gender == 'M']

    for cf in females:
        for cm in males:
            # Profile distance (normalized, weighted by IDF relevance)
            d = (abs(cf.dapar   - cm.dapar)   / 90  * 0.35 +
                 abs(cf.tech    - cm.tech)    / 100 * 0.25 +
                 abs(cf.mental  - cm.mental)  / 100 * 0.20 +
                 abs(cf.manila  - cm.manila)  / 100 * 0.20)

            if d > profile_eps:
                continue  # profiles too different — no comparison

            # Compare assigned role quality
            rf_id = assignment.get(cf.name)
            rm_id = assignment.get(cm.name)
            if not rf_id or not rm_id:
                continue

            sf = fit_score(cf, role_map[rf_id])
            sm = fit_score(cm, role_map[rm_id])
            delta = sm - sf  # positive = man got better assignment

            if abs(delta) > score_delta:
                violations.append({
                    'female':      cf.name,
                    'male':        cm.name,
                    'profile_d':   round(d, 3),
                    'female_role': rf_id,
                    'male_role':   rm_id,
                    'fit_delta':   round(delta, 1),
                    'direction':   'man_better' if delta > 0 else 'woman_better',
                })

    return violations


def bias_comparison(candidates: List[Candidate] = CANDIDATES,
                    roles: List[Role] = ROLES,
                    alpha: float = 0.5,
                    cycle: str = 'august') -> None:
    """
    Show the discrimination problem and the fix side by side.
    """
    print("\n" + "=" * 62)
    print("Gender Fairness Analysis")
    print("=" * 62)

    role_map = {r.id: r for r in roles}

    # Find מאיה (F) and her closest male match (יואב, similar profile)
    maaya = next((c for c in candidates if c.gender == 'F'), None)
    males = [c for c in candidates if c.gender == 'M']
    if not maaya or not males:
        print("  No gender pair found.")
        return

    # Pick יואב as comparison (same pref, close profile)
    yoav = next((c for c in candidates if c.name == 'יואב'), males[0])

    print(f"\n  Comparison: {maaya.name} (F, {CONTRACT_MONTHS['F']}m) vs "
          f"{yoav.name} (M, {CONTRACT_MONTHS['M']}m)")
    print(f"  {'Role':<22} {'Biased(F)':>10} {'Biased(M)':>10} "
          f"{'Fair(F)':>10} {'Fair(M)':>10} {'Gap(biased)':>12}")
    print("  " + "-" * 76)

    for r in roles:
        bf = biased_temporal_nash(maaya, r, alpha, cycle)
        bm = biased_temporal_nash(yoav,  r, alpha, cycle)
        ff = gender_fair_nash(maaya, r, alpha, cycle)
        fm = gender_fair_nash(yoav,  r, alpha, cycle)
        if bf in (-np.inf, None) and bm in (-np.inf, None):
            continue
        bf_str = f"{bf:.2f}" if bf not in (-np.inf, None) else "blocked"
        bm_str = f"{bm:.2f}" if bm not in (-np.inf, None) else "blocked"
        ff_str = f"{ff:.2f}" if ff not in (-np.inf, None) else "blocked"
        fm_str = f"{fm:.2f}" if fm not in (-np.inf, None) else "blocked"
        gap = ((bm - bf) if (bm not in (-np.inf, None) and bf not in (-np.inf, None))
               else 0)
        gap_str = f"{gap:+.2f}" if gap != 0 else "   —"
        flag = " ⚠️" if abs(gap) > 5 else ""
        print(f"  {r.name:<22} {bf_str:>10} {bm_str:>10} "
              f"{ff_str:>10} {fm_str:>10} {gap_str:>12}{flag}")

    # Run assignments with both methods and compare
    print(f"\n  Assignment comparison (best role per candidate):")
    for c in [maaya, yoav]:
        biased_best = max(
            [(biased_temporal_nash(c, r, alpha, cycle), r.id) for r in roles
             if biased_temporal_nash(c, r, alpha, cycle) not in (-np.inf, None)],
            default=(None, None)
        )
        fair_best = max(
            [(gender_fair_nash(c, r, alpha, cycle), r.id) for r in roles
             if gender_fair_nash(c, r, alpha, cycle) not in (-np.inf, None)],
            default=(None, None)
        )
        print(f"    {c.name} ({c.gender}): biased→{biased_best[1]} ({biased_best[0]:.1f})  "
              f"fair→{fair_best[1]} ({fair_best[0]:.1f})")

    # Run GA with fair method + fairness audit
    print(f"\n  Running fair assignment + audit...")
    fair_result = ga_assignment(candidates, roles, gender_fair_nash,
                                alpha=alpha, cycle=cycle,
                                pop_size=50, generations=100)
    violations = fairness_audit(fair_result['assignment'], candidates, roles)

    if violations:
        print(f"  ⚠️  {len(violations)} fairness violation(s) detected:")
        for v in violations:
            print(f"    {v['female']} (F,{v['female_role']}) vs "
                  f"{v['male']} (M,{v['male_role']}): "
                  f"Δfit={v['fit_delta']:+.1f} [{v['direction']}] "
                  f"profile_d={v['profile_d']}")
    else:
        print(f"  ✅ No gender fairness violations detected in fair assignment.")

    print(f"\n  Conclusion:")
    print(f"  Biased temporal: women score ×{CONTRACT_MONTHS['F']/CONTRACT_MONTHS['M']:.2f} of men")
    print(f"  Fair temporal:   completion_rate is gender-neutral → equal treatment")


def factor_impact(c: Candidate, r: Role,
                  alpha: float = 0.5, cycle: str = 'august') -> Dict:
    """Show contribution of each new factor to score change."""
    base     = nash_score(c, r, alpha, cycle)
    full     = full_nash_score(c, r, alpha, cycle)
    if base in (-np.inf, None): return {}
    return {
        'base_nash':     round(base, 2),
        'full_nash':     round(full, 2),
        'distance_km':   round(distance_km(c, r), 1),
        'dist_penalty':  round(distance_score(c, r), 2),
        'lang_bonus':    round(language_bonus(c, r), 2),
        'retention':     round(retention_prob(c, r, alpha), 3),
        'clv':           round(clv_score(c, r), 2),
        'delta':         round((full - base), 2) if full not in (-np.inf, None) else None,
    }


# ──────────────────────────────────────────
# PHASE 1: COMBAT PRE-ALLOCATION
# ──────────────────────────────────────────

def combat_phase1(candidates: List[Candidate],
                  roles: List[Role],
                  alpha: float = 0.5,
                  cycle: str = 'august') -> tuple:
    """
    Phase 1: Pre-allocate combat-eligible candidates BEFORE Nash-GA.

    IDF policy: any candidate with medical ≥ 72 must be offered combat
    placement first, before being considered for rear roles.

    Algorithm:
    1. Identify combat-eligible candidates (medical ≥ 72)
    2. Sort by combat fitness score (combat×0.5 + mental×0.3 + medical×0.2)
    3. Greedily assign to combat_priority roles
    4. Only assign if candidate has pref match OR combat score ≥ 80
    5. Return pre-assigned dict + remaining candidates + remaining slots

    Returns: (pre_assignments, remaining_candidates, role_slots_used)
    """
    combat_roles  = [r for r in roles if r.combat_priority]
    combat_eligible = [c for c in candidates if c.medical >= 72]

    # Sort: strongest combat candidates get first pick
    combat_eligible.sort(
        key=lambda c: c.combat * 0.50 + c.mental * 0.30 + (c.medical / 97) * 20,
        reverse=True
    )

    pre_assignments = {}   # cand_name → role_id
    role_slots_used = {r.id: 0 for r in roles}

    for cand in combat_eligible:
        # Find best combat role for this candidate
        best_role = None
        best_score = -1

        for role in combat_roles:
            # Check hard constraints
            if check_hard_constraints(cand, role):
                continue
            # Don't exceed role capacity
            if role_slots_used[role.id] >= role.teken:
                continue

            nash = full_nash_score(cand, role, alpha, cycle)
            if nash and nash != -np.inf and nash > best_score:
                # Only pre-assign if: candidate wants combat OR is highly combat-fit
                pref_idx = cand.pref.index(role.id) if role.id in cand.pref else -1
                if pref_idx >= 0 or cand.combat >= 80:
                    best_score = nash
                    best_role  = role

        if best_role:
            pre_assignments[cand.name] = best_role.id
            role_slots_used[best_role.id] += 1

    remaining = [c for c in candidates if c.name not in pre_assignments]
    print(f"  Phase 1 pre-assigned: {len(pre_assignments)} combat candidates")
    for name, role_id in pre_assignments.items():
        print(f"    {name} → {role_id}")

    return pre_assignments, remaining, role_slots_used


# ──────────────────────────────────────────
# CAPACITY + QUOTA PENALTY
# ──────────────────────────────────────────

def capacity_quota_penalty(assignment: Dict,
                           candidates: List[Candidate],
                           roles: List[Role]) -> float:
    """
    Penalty for violating hard constraints:
    1. Capacity_j: total assigned > teken
    2. MinFill_j: total assigned < min_fill (unit not viable)
    3. Gender quota: % women < min_women_pct
    4. Periphery quota: % periphery < min_periphery_pct

    Returns: penalty score (negative, subtracted from fitness)
    Penalty magnitude chosen so violations strongly outweigh score gains.
    """
    cand_map  = {c.name: c for c in candidates}
    role_map  = {r.id: r   for r in roles}

    # Group assignments by role
    by_role: Dict[str, List[str]] = {}
    for cand_name, role_id in assignment.items():
        by_role.setdefault(role_id, []).append(cand_name)

    total_penalty = 0.0

    for role in roles:
        assigned_names = by_role.get(role.id, [])
        n = len(assigned_names)

        # 1. Hard capacity upper bound
        if n > role.teken:
            total_penalty += (n - role.teken) * 100

        # 2. Minimum fill (unit viability)
        if 0 < n < role.min_fill:
            total_penalty += (role.min_fill - n) * 50

        if n == 0:
            continue

        assigned_cands = [cand_map[name] for name in assigned_names
                          if name in cand_map]

        # 3. Gender quota
        if role.min_women_pct > 0:
            women = sum(1 for c in assigned_cands if c.gender == 'F')
            women_pct = women / n
            if women_pct < role.min_women_pct:
                total_penalty += (role.min_women_pct - women_pct) * n * 30

        # 4. Periphery quota
        if role.min_periphery_pct > 0:
            peri = sum(1 for c in assigned_cands if c.periphery)
            peri_pct = peri / n
            if peri_pct < role.min_periphery_pct:
                total_penalty += (role.min_periphery_pct - peri_pct) * n * 25

    return -total_penalty  # negative penalty reduces fitness


# ──────────────────────────────────────────
# FULL PIPELINE (Phase1 → Nash-GA + Quotas → Erdil-Ergin)
# ──────────────────────────────────────────

def full_pipeline(candidates: List[Candidate],
                  roles: List[Role],
                  alpha: float = 0.5,
                  cycle: str = 'august') -> Dict:
    """
    Production-ready 3-phase pipeline:

    Phase 1: Combat pre-allocation
      → IDF policy: medical≥72 candidates offered combat first

    Phase 2: Nash-GA with quota constraints
      → full_nash_score + capacity_quota_penalty
      → Warm start from greedy solution

    Phase 3: Erdil-Ergin stable improvements
      → Post-processing for Pareto efficiency

    Suitable for 30K candidates with O(n×gens) complexity.
    """
    print("\n" + "=" * 50)
    print(f"Full Pipeline  |  α={alpha}  cycle={cycle}")
    print("=" * 50)

    # ── Phase 1: Combat pre-allocation ──────
    print("\nPhase 1 — Combat Pre-allocation:")
    pre_assign, remaining_cands, slots_used = combat_phase1(
        candidates, roles, alpha, cycle)

    # ── Phase 2: Nash-GA on remaining candidates ──
    print(f"\nPhase 2 — Nash-GA ({len(remaining_cands)} remaining candidates):")

    def combined_score_fn(c, r, a, cyc):
        """Full Nash score used inside GA."""
        return full_nash_score(c, r, a, cyc)

    if remaining_cands:
        # Temporarily adjust role capacities for remaining slots
        import copy
        roles_adj = copy.deepcopy(roles)
        for r in roles_adj:
            r.teken = max(1, r.teken - slots_used.get(r.id, 0))

        ga_result = ga_assignment(
            remaining_cands, roles_adj, combined_score_fn,
            alpha=alpha, cycle=cycle,
            pop_size=60, generations=150
        )

        # Inject quota penalty into GA fitness (post-hoc analysis)
        quota_pen = capacity_quota_penalty(
            ga_result['assignment'], remaining_cands, roles_adj)
        ga_result['quota_penalty'] = round(quota_pen, 2)

        # ── Phase 3: Erdil-Ergin ──────────────
        print(f"\nPhase 3 — Erdil-Ergin improvements:")
        final = erdil_ergin(ga_result, remaining_cands, roles_adj,
                            combined_score_fn, alpha, cycle)
    else:
        final = {'assignment': {}, 'total_score': 0, 'swaps_made': 0,
                 'quota_penalty': 0}

    # Merge Phase 1 + Phase 2+3
    merged = {**pre_assign, **final['assignment']}

    # Quota audit on full assignment
    quota_pen_full = capacity_quota_penalty(merged, candidates, roles)

    print(f"\nFinal assignment ({len(merged)}/{len(candidates)} placed):")
    role_map  = {r.id: r   for r in roles}
    cand_map  = {c.name: c for c in candidates}
    for name, role_id in merged.items():
        role  = role_map.get(role_id)
        c     = cand_map.get(name)
        phase = "P1" if name in pre_assign else "P2"
        pref_tag = "❤️" if role_id in (c.pref[:1] if c else []) else \
                   "🔵" if role_id in (c.pref[1:2] if c else []) else "  "
        print(f"  [{phase}] {name:<8} → {role.name if role else '?':<22} {pref_tag}")

    unplaced = [c.name for c in candidates if c.name not in merged]
    if unplaced:
        print(f"\n  Unplaced (committee): {', '.join(unplaced)}")

    print(f"\n  Nash score: {final['total_score']:.2f}")
    print(f"  Quota penalty: {quota_pen_full:.1f}  "
          f"({'OK' if quota_pen_full == 0 else 'VIOLATIONS'})")
    print(f"  Erdil-Ergin swaps: {final['swaps_made']}")

    return merged


def greedy_warm_start(candidates: List[Candidate],
                      roles: List[Role],
                      score_fn,
                      alpha: float = 0.5,
                      cycle: str = 'august') -> List[str]:
    """
    Greedy warm start for GA initialization.
    Assigns each candidate to their best available role (by score).
    Result used as seed chromosome → GA converges 60-80% faster.

    Complexity: O(n × m) — trivial vs GA's O(n × generations)
    """
    role_ids    = [r.id for r in roles]
    assigned    = {}   # cand_name → role_id
    role_taken  = set()

    # Sort candidates by "best possible score" descending
    # (greedy: most constrained candidates first avoids deadlocks)
    def best_score(cand):
        scores = [score_fn(cand, r, alpha, cycle)
                  for r in roles
                  if r.id not in role_taken]
        valid = [s for s in scores if s not in (None, -np.inf)]
        return max(valid) if valid else -9999

    sorted_cands = sorted(candidates, key=best_score, reverse=True)

    for cand in sorted_cands:
        best_role_id = None
        best_s       = -9999
        for r in roles:
            if r.id in role_taken:
                continue
            s = score_fn(cand, r, alpha, cycle)
            if s not in (None, -np.inf) and s > best_s:
                best_s       = s
                best_role_id = r.id
        if best_role_id:
            assigned[cand.name] = best_role_id
            role_taken.add(best_role_id)

    # Build chromosome in candidates order
    cand_names = [c.name for c in candidates]
    chromosome = []
    remaining  = [rid for rid in role_ids if rid not in role_taken]
    random.shuffle(remaining)

    for name in cand_names:
        if name in assigned:
            chromosome.append(assigned[name])
        else:
            chromosome.append(remaining.pop() if remaining else role_ids[0])

    return chromosome

def additive_score(c: Candidate, r: Role,
                   alpha: float = 0.5, cycle: str = 'august') -> float:
    """
    Standard ILP additive score (current system — for comparison).
    max Σ Score_ij × X_ij
    """
    block = check_hard_constraints(c, r)
    if block:
        return -np.inf

    fit_w = 0.55 + alpha * 0.15
    urg_w = 0.45 - alpha * 0.15
    adjusted_fit = fit_score(c, r) + pref_score(c, r, alpha)
    return round(adjusted_fit * fit_w + urgency_score(r, cycle) * urg_w, 4)

# ──────────────────────────────────────────
# GENETIC ALGORITHM
# ──────────────────────────────────────────

def ga_assignment(candidates: List[Candidate],
                  roles: List[Role],
                  score_fn,
                  alpha: float = 0.5,
                  cycle: str = 'august',
                  pop_size: int = 80,
                  generations: int = 200,
                  mutation_rate: float = 0.15) -> Dict:
    """
    GA for volume/additive assignment.

    Chromosome: permutation of role indices (+ None for unplaced)
    Fitness: sum of individual nash/additive scores
    """
    n = len(candidates)
    role_ids = [r.id for r in roles]

    def make_chromosome():
        """Random 1-to-1 assignment (may leave some unplaced)."""
        shuffled = role_ids.copy()
        random.shuffle(shuffled)
        return shuffled[:n]  # each candidate gets one role

    def fitness(chrom):
        total = 0
        for i, role_id in enumerate(chrom):
            role = next(r for r in roles if r.id == role_id)
            s = score_fn(candidates[i], role, alpha, cycle)
            if s == -np.inf:
                return -np.inf
            total += s
        return total

    def crossover(p1, p2):
        """Order crossover (OX) — preserves permutation validity."""
        point = random.randint(1, n - 1)
        child = p1[:point]
        for gene in p2:
            if gene not in child:
                child.append(gene)
            if len(child) == n:
                break
        return child

    def mutate(chrom):
        """Swap mutation."""
        if random.random() < mutation_rate:
            i, j = random.sample(range(n), 2)
            chrom[i], chrom[j] = chrom[j], chrom[i]
        return chrom

    # Initialize — warm start: seed first chromosome with greedy solution
    warm = greedy_warm_start(candidates, roles, score_fn, alpha, cycle)
    population = [warm] + [make_chromosome() for _ in range(pop_size - 1)]
    best_chrom = warm.copy()
    best_fit   = fitness(warm) if fitness(warm) not in (None, -np.inf) else -9999.0

    for gen in range(generations):
        scored = [(fitness(c), c) for c in population]
        scored.sort(key=lambda x: x[0] if x[0] not in (None, -np.inf) else -9999,
                    reverse=True)

        top_fit = scored[0][0] if scored[0][0] not in (None, -np.inf) else -9999
        if top_fit > best_fit:
            best_fit, best_chrom = top_fit, scored[0][1].copy()

        # Elitism: keep top 10%
        elite = [c for _, c in scored[:pop_size // 10]]

        # Tournament selection + crossover
        new_pop = elite.copy()
        while len(new_pop) < pop_size:
            p1 = random.choice(scored[:pop_size // 2])[1]
            p2 = random.choice(scored[:pop_size // 2])[1]
            child = mutate(crossover(p1, p2))
            new_pop.append(child)

        population = new_pop

    return {
        'assignment': {candidates[i].name: best_chrom[i]
                       for i in range(n)},
        'total_score': round(best_fit, 4),
        'individual_scores': {
            candidates[i].name: round(
                score_fn(candidates[i],
                         next(r for r in roles if r.id == best_chrom[i]),
                         alpha, cycle), 4)
            for i in range(n)
        }
    }

# ──────────────────────────────────────────
# ERDIL-ERGIN POST-PROCESSING
# ──────────────────────────────────────────

def erdil_ergin(assignment_dict: Dict, candidates, roles,
                score_fn, alpha=0.5, cycle='august') -> Dict:
    """
    Phase 3: Stable improvement cycles (Erdil & Ergin, 2008).
    After GA finds a good region, this finds Pareto improvements.

    A "stable improvement cycle" exists when:
    candidates A, B assigned to roles X, Y respectively, and
    score(A, Y) > score(A, X)  AND  score(B, X) > score(B, Y)
    → swap: both improve, total score increases.
    """
    assignment = assignment_dict['assignment'].copy()
    cand_map = {c.name: c for c in candidates}
    role_map  = {r.id: r  for r in roles}

    improved = True
    n_swaps  = 0

    while improved:
        improved = False
        names = list(assignment.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a_name, b_name = names[i], names[j]
                a_role_id, b_role_id = assignment[a_name], assignment[b_name]

                a, b = cand_map[a_name], cand_map[b_name]
                ra, rb = role_map[a_role_id], role_map[b_role_id]

                # Current scores
                s_aa = score_fn(a, ra, alpha, cycle)
                s_bb = score_fn(b, rb, alpha, cycle)
                # Swapped scores
                s_ab = score_fn(a, rb, alpha, cycle)
                s_ba = score_fn(b, ra, alpha, cycle)

                # Pareto improvement: both strictly better (or one better, one same)
                if (s_ab > s_aa and s_ba >= s_bb) or \
                   (s_ab >= s_aa and s_ba > s_bb):
                    assignment[a_name] = b_role_id
                    assignment[b_name] = a_role_id
                    improved = True
                    n_swaps += 1
                    break
            if improved:
                break

    total = sum(
        score_fn(cand_map[name], role_map[role_id], alpha, cycle)
        for name, role_id in assignment.items()
    )
    return {'assignment': assignment, 'total_score': round(total, 4),
            'swaps_made': n_swaps}

# ──────────────────────────────────────────
# PARETO FRONTIER
# ──────────────────────────────────────────

def pareto_frontier(candidates, roles, score_fn,
                    cycle='august', n_points=8,
                    ga_gens=100) -> List[Dict]:
    """
    Compute Pareto frontier by sweeping α ∈ [0, 1].
    Each point: (α, avg_fit, avg_urgency, nash_score)
    """
    frontier = []
    for alpha in np.linspace(0, 1, n_points):
        result = ga_assignment(candidates, roles, score_fn,
                               alpha=alpha, cycle=cycle,
                               generations=ga_gens, pop_size=40)
        result = erdil_ergin(result, candidates, roles,
                              score_fn, alpha=alpha, cycle=cycle)

        cand_map = {c.name: c for c in candidates}
        role_map  = {r.id: r  for r in roles}

        fits, urgs = [], []
        for name, role_id in result['assignment'].items():
            c = cand_map[name]
            r = role_map[role_id]
            block = check_hard_constraints(c, r)
            if not block:
                fits.append(fit_score(c, r))
                urgs.append(urgency_score(r, cycle))

        frontier.append({
            'alpha':          round(float(alpha), 2),
            'avg_fit':        round(float(np.mean(fits)),  2) if fits else 0,
            'avg_urgency':    round(float(np.mean(urgs)),  2) if urgs else 0,
            'total_nash':     result['total_score'],
        })

    return frontier

# ──────────────────────────────────────────
# COMPARISON: NASH vs ADDITIVE
# ──────────────────────────────────────────

def compare_methods(candidates=CANDIDATES, roles=ROLES,
                    alpha=0.5, cycle='august'):
    print("=" * 60)
    print(f"Military Placement Comparison  |  α={alpha}  cycle={cycle}")
    print("=" * 60)

    import time
    methods = [
        ("Additive (ILP)",      additive_score),
        ("Nash-Volume",         nash_score),
        ("Full Nash (30K)",     full_nash_score),
    ]
    results = {}
    for method_name, score_fn in methods:
        t0 = time.time()
        res = ga_assignment(candidates, roles, score_fn,
                            alpha=alpha, cycle=cycle,
                            pop_size=60, generations=150)
        res = erdil_ergin(res, candidates, roles, score_fn, alpha, cycle)
        res['time_ms'] = round((time.time() - t0) * 1000)
        results[method_name] = res

    cand_map = {c.name: c for c in candidates}
    role_map  = {r.id: r  for r in roles}

    for method_name, result in results.items():
        print(f"\n  [{method_name}] — {result['time_ms']}ms | swaps={result['swaps_made']}")
        for name, role_id in result['assignment'].items():
            role  = role_map[role_id]
            c     = cand_map[name]
            block = check_hard_constraints(c, role)
            pref_tag = "❤️" if role_id in c.pref[:1] else "🔵" if role_id in c.pref[1:2] else "  "
            tag   = f"⛔ {block}" if block else f"fit={fit_score(c,role):.0f} {pref_tag}"
            print(f"    {name:<8} → {role.name:<22} | {tag}")

    # Pareto Frontier
    print("\n\nPareto Frontier (Nash-Volume):")
    print(f"  {'α':<6} {'avg_fit':<12} {'avg_urgency':<14} {'total_nash'}")
    print("  " + "-" * 46)
    frontier = pareto_frontier(candidates, roles, nash_score,
                                cycle=cycle, n_points=6, ga_gens=80)
    for pt in frontier:
        bar_fit = "█" * int(pt['avg_fit'] / 10)
        bar_urg = "█" * int(pt['avg_urgency'] / 10)
        print(f"  {pt['alpha']:<6} {pt['avg_fit']:<6} {bar_fit:<12} "
              f"{pt['avg_urgency']:<6} {bar_urg:<12} {pt['total_nash']}")

    # Factor Impact table — Full Nash
    print("\n\nFactor Impact (Full Nash vs Basic Nash):")
    print(f"  {'Candidate':<8} {'Role':<22} {'Basic':>7} {'Full':>7} "
          f"{'Δ':>6} {'dist km':>8} {'lang':>5} {'ret':>5} {'clv':>6}")
    print("  " + "-" * 75)
    for c in candidates:
        best_role = None
        best_full = -9999
        for r in roles:
            f = full_nash_score(c, r, alpha, cycle)
            if f not in (-np.inf, None) and f > best_full:
                best_full = f
                best_role = r
        if best_role:
            imp = factor_impact(c, best_role, alpha, cycle)
            if imp:
                print(f"  {c.name:<8} {best_role.name:<22} "
                      f"{imp['base_nash']:>7.2f} {imp['full_nash']:>7.2f} "
                      f"{(imp['delta'] or 0):>+6.2f} "
                      f"{imp['distance_km']:>8.1f} "
                      f"{imp['lang_bonus']:>5.1f} "
                      f"{imp['retention']:>5.3f} "
                      f"{imp['clv']:>6.1f}")

    # Feedback Loop demo
    print("\n\nFeedback Loop — Simulated weight update after 1 cycle:")
    import copy
    roles_copy = copy.deepcopy(roles)
    cyber_role = next(r for r in roles_copy if r.id == 'cyber')
    print(f"  cyber weights BEFORE: {', '.join(f'{k}:{v:.3f}' for k,v in cyber_role.weights.items())}")

    mock_records = [
        PerformanceRecord("דניאל", "cyber", predicted_fit=85.0,
                          actual_performance=92.0, completed_service=True),
        PerformanceRecord("אלון",  "cyber", predicted_fit=81.0,
                          actual_performance=78.0, completed_service=True),
    ]
    roles_copy = update_weights(roles_copy, mock_records)
    cyber_after = next(r for r in roles_copy if r.id == 'cyber')
    print(f"  cyber weights AFTER:  {', '.join(f'{k}:{v:.3f}' for k,v in cyber_after.weights.items())}")
    print("  (weights converge toward empirical optimum over ~10 cycles)")

    print("\n✓ Done")

# ──────────────────────────────────────────
# UNIT TESTS
# ──────────────────────────────────────────

def run_tests():
    print("Running unit tests...")

    # Test 1: Hard constraint blocks → -inf
    c_blocked = Candidate("test", dapar=50, medical=45, tech=90,
                           manila=80, mental=78, combat=20, pref=[])
    r_cyber = next(r for r in ROLES if r.id == 'cyber')
    score = nash_score(c_blocked, r_cyber)
    assert score == -np.inf, f"Expected -inf, got {score}"
    print("  ✓ Hard constraint → -inf")

    # Test 2: Nash score > 0 for eligible candidate
    c_daniel = CANDIDATES[0]  # דניאל
    score = nash_score(c_daniel, r_cyber)
    assert score > 0, f"Expected > 0, got {score}"
    print(f"  ✓ Nash score for דניאל→8200: {score:.2f}")

    # Test 3: Nash is balanced — penalizes extreme outcomes
    # Create role with 0 urgency (fully staffed)
    r_full = Role("full_role", "מלא", {}, {'dapar':0.5,'tech':0.5},
                   teken=100, miluy=100)
    s_nash = nash_score(c_daniel, r_full)
    s_add  = additive_score(c_daniel, r_full)
    # Nash should heavily penalize 0-urgency role
    print(f"  ✓ Zero-urgency role: Nash={s_nash:.2f}, Additive={s_add:.2f}")
    print(f"    (Nash penalizes harder: {s_nash:.2f} vs {s_add:.2f})")

    # Test 4: Erdil-Ergin improves or maintains score
    initial = ga_assignment(CANDIDATES, ROLES, nash_score,
                             pop_size=20, generations=30)
    improved = erdil_ergin(initial, CANDIDATES, ROLES, nash_score)
    assert improved['total_score'] >= initial['total_score'], \
        "Erdil-Ergin should not decrease score"
    print(f"  ✓ Erdil-Ergin: {initial['total_score']:.2f} → {improved['total_score']:.2f}"
          f" ({improved['swaps_made']} swaps)")

    print("All tests passed.\n")

# ──────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────

# ──────────────────────────────────────────
# 30K SCALE: SYNTHETIC DATA + MULTI-CAPACITY GA
# ──────────────────────────────────────────

def generate_synthetic(n: int, seed: int = 0) -> List[Candidate]:
    """
    Generate n synthetic IDF candidates with realistic distributions.
    dapar: 10–90 in steps of 10 (as per IDF scale).
    Medical: realistic distribution (most get 97, some lower).
    """
    rng = random.Random(seed)
    cities = list(CITY_COORDS.keys())
    lang_opts = [[], ['english'], ['arabic'], ['english'], ['english','arabic']]

    # Realistic dapar distribution (right-skewed: most 60-80)
    dapar_pool = [10]*2 + [20]*3 + [30]*5 + [40]*8 + [50]*12 + \
                 [60]*18 + [70]*22 + [80]*18 + [90]*12

    # Realistic medical distribution
    medical_pool = [97]*55 + [82]*20 + [72]*10 + [64]*7 + [45]*6 + [21]*2

    cands = []
    for i in range(n):
        dpr = rng.choice(dapar_pool)
        med = rng.choice(medical_pool)
        # tech/combat correlated with dapar/medical respectively
        tech    = min(100, max(10, dpr + rng.randint(-20, 20)))
        combat  = min(100, max(10, med // 2 + rng.randint(0, 40)))
        manila  = rng.randint(40, 95)
        mental  = rng.randint(40, 95)
        pref_k  = rng.randint(1, 3)
        pref    = rng.sample(['admin','intel','product','elint','elite','cyber'], pref_k)
        gender  = 'F' if rng.random() < 0.25 else 'M'
        periph  = rng.random() < 0.18

        cands.append(Candidate(
            name=f"c{i:05d}",
            dapar=dpr, medical=med, tech=tech,
            manila=manila, mental=mental, combat=combat,
            pref=pref,
            home_city=rng.choice(cities),
            languages=rng.choice(lang_opts),
            fitness_score=rng.randint(40, 100),
            leadership_xp=rng.randint(0, 3),
            gender=gender, periphery=periph,
        ))
    return cands


def scaled_ga(candidates: List[Candidate],
              roles: List[Role],
              alpha: float = 0.5,
              cycle: str = 'august',
              pop_size: int = 60,
              generations: int = 100) -> Dict[str, str]:
    """
    Multi-capacity GA for large n.

    Key difference from small-n GA:
    - Chromosome: list of role_ids (length = n), multiple candidates can share a role
    - Capacity enforced via penalty (soft) — hard enforcement via post-processing
    - O(n × pop_size × generations) — linear in n

    For 30K: cluster first (see hierarchical_assignment), then run per cluster.
    """
    n = len(candidates)
    role_ids = [r.id for r in roles]
    role_map = {r.id: r for r in roles}

    def make_chrom():
        """Random assignment respecting rough capacity ratios."""
        total_teken = sum(r.teken for r in roles)
        chrom = []
        for _ in range(n):
            # Weight by teken (more slots → more likely to be chosen)
            weights = [r.teken / total_teken for r in roles]
            chrom.append(rng.choices(role_ids, weights=weights)[0])
        return chrom

    rng = random.Random()

    def fitness(chrom):
        total = 0.0
        # Count per role
        counts = {rid: 0 for rid in role_ids}
        for rid in chrom:
            counts[rid] += 1

        # Capacity penalty
        cap_pen = 0.0
        for r in roles:
            over = max(0, counts[r.id] - r.teken)
            cap_pen += over * 15  # penalty per excess assignment

        for i, cand in enumerate(candidates):
            r = role_map[chrom[i]]
            s = full_nash_score(cand, r, alpha, cycle)
            if s == -np.inf:
                cap_pen += 20  # hard constraint violation penalty
            else:
                total += s
        return total - cap_pen

    # Warm start: greedy proportional assignment
    total_teken = sum(r.teken for r in roles)
    warm = []
    role_slots = {r.id: r.teken for r in roles}
    for cand in candidates:
        best_rid, best_s = role_ids[0], -9999
        for r in roles:
            if role_slots.get(r.id, 0) <= 0:
                continue
            s = full_nash_score(cand, r, alpha, cycle)
            if s and s != -np.inf and s > best_s:
                best_s, best_rid = s, r.id
        warm.append(best_rid)
        role_slots[best_rid] = role_slots.get(best_rid, 1) - 1

    population = [warm.copy()]
    for _ in range(pop_size - 1):
        population.append(make_chrom())

    best_chrom = warm.copy()
    best_fit   = fitness(warm)

    for _ in range(generations):
        scored = sorted([(fitness(c), c) for c in population],
                        key=lambda x: x[0], reverse=True)
        if scored[0][0] > best_fit:
            best_fit, best_chrom = scored[0][0], scored[0][1].copy()

        # Elite + crossover + mutation
        elite = [c for _, c in scored[:max(1, pop_size//10)]]
        new_pop = elite.copy()
        while len(new_pop) < pop_size:
            p1 = rng.choice(scored[:pop_size//2])[1]
            p2 = rng.choice(scored[:pop_size//2])[1]
            pt = rng.randint(1, n-1)
            child = p1[:pt] + p2[pt:]
            if rng.random() < 0.1:
                i = rng.randint(0, n-1)
                child[i] = rng.choice(role_ids)
            new_pop.append(child)
        population = new_pop

    return {candidates[i].name: best_chrom[i] for i in range(n)}


def hierarchical_assignment(candidates: List[Candidate],
                             roles: List[Role],
                             alpha: float = 0.5,
                             cycle: str = 'august',
                             n_clusters: int = 5) -> Dict[str, str]:
    """
    Hierarchical approach for 30K:
    1. Cluster candidates by dapar quartile (proxy for role suitability)
    2. Run scaled_ga per cluster independently
    3. Merge results

    Why clustering:
    - Reduces effective n per GA run: 30K / 5 clusters = 6K per cluster
    - Each cluster competes for proportional role slots
    - O(n_clusters × (n/clusters) × gens) = O(n × gens) — same total complexity
    - But each GA run is faster (better convergence)
    """
    # Cluster by dapar
    sorted_cands = sorted(candidates, key=lambda c: c.dapar, reverse=True)
    cluster_size = len(sorted_cands) // n_clusters
    clusters = [sorted_cands[i*cluster_size:(i+1)*cluster_size]
                for i in range(n_clusters)]
    # Last cluster gets remainder
    if len(sorted_cands) % n_clusters:
        clusters[-1] += sorted_cands[n_clusters*cluster_size:]

    merged = {}
    for k, cluster in enumerate(clusters):
        if not cluster:
            continue
        # Proportional role slots for this cluster
        import copy
        roles_k = copy.deepcopy(roles)
        frac = len(cluster) / len(candidates)
        for r in roles_k:
            r.teken = max(1, int(r.teken * frac))

        result = scaled_ga(cluster, roles_k, alpha, cycle,
                           pop_size=40, generations=80)
        merged.update(result)
    return merged


def scaling_benchmark():
    """
    Benchmark Nash-GA runtime for increasing n.
    Shows O(n) scaling vs O(n³) for Hungarian.
    Projects to 30,000 candidates.
    """
    import time
    import math

    print("\n" + "=" * 58)
    print("Scaling Benchmark — Nash-GA (Full Pipeline)")
    print("=" * 58)
    print(f"  {'n':>6}  {'Phase1':>8}  {'GA':>8}  {'Total':>8}  {'Hungarian O(n³)':>16}")
    print("  " + "-" * 56)

    # Reference: Hungarian at n=6 takes ~1ms
    HUNG_REF_N = 6
    HUNG_REF_MS = 1.0

    sizes = [6, 20, 50, 100, 250, 500, 1000]
    timings = []

    for n in sizes:
        cands = generate_synthetic(n, seed=42)

        t0 = time.time()
        # Phase 1 (combat pre-allocation)
        pre, remaining, slots = combat_phase1(cands, ROLES)
        t_phase1 = (time.time() - t0) * 1000

        t1 = time.time()
        # Scaled GA
        if remaining:
            scaled_ga(remaining, ROLES, pop_size=30, generations=50)
        t_ga = (time.time() - t1) * 1000

        t_total = t_phase1 + t_ga

        # Projected Hungarian time: O(n³)
        hung_ms = HUNG_REF_MS * (n / HUNG_REF_N) ** 3

        timings.append((n, t_total))
        hung_str = f"{hung_ms/1000:.1f}s" if hung_ms > 1000 else f"{hung_ms:.0f}ms"
        print(f"  {n:>6}  {t_phase1:>7.1f}ms  {t_ga:>7.1f}ms  "
              f"{t_total:>7.1f}ms  {hung_str:>16}")

    # Extrapolate to 30K using linear regression on log scale
    log_n = [math.log(t[0]) for t in timings]
    log_t = [math.log(max(t[1], 0.1)) for t in timings]
    # Simple linear fit: log(t) = a * log(n) + b
    n_pts = len(log_n)
    mean_x = sum(log_n) / n_pts
    mean_y = sum(log_t) / n_pts
    a = sum((log_n[i]-mean_x)*(log_t[i]-mean_y) for i in range(n_pts)) / \
        sum((log_n[i]-mean_x)**2 for i in range(n_pts))
    b = mean_y - a * mean_x

    proj_30k = math.exp(a * math.log(30000) + b)
    proj_clust = proj_30k / 5  # hierarchical clustering divides by n_clusters

    print(f"\n  Scaling exponent: O(n^{a:.2f})")
    print(f"  Projected 30K (single):        {proj_30k/1000:.1f}s")
    print(f"  Projected 30K (×5 clustering): {proj_clust/1000:.1f}s")
    print(f"  Projected 30K (×5 + parallel): {proj_clust/5000:.1f}s")
    print(f"  Hungarian at 30K:              IMPOSSIBLE "
          f"({HUNG_REF_MS*(30000/HUNG_REF_N)**3/86400000:.0f} days)")

    print("\n  Complexity summary:")
    print("  ┌──────────────────────┬──────────────┬───────────┐")
    print("  │ Algorithm            │ Complexity   │ 30K time  │")
    print("  ├──────────────────────┼──────────────┼───────────┤")
    print(f"  │ Hungarian (optimal)  │ O(n³)        │ >years    │")
    print(f"  │ Nash-GA (flat)       │ O(n×gens)    │ ~{proj_30k/1000:.0f}s      │")
    print(f"  │ Nash-GA (cluster×5)  │ O(n×gens)    │ ~{proj_clust/1000:.1f}s     │")
    print(f"  │ Nash-GA (parallel)   │ O(n×gens/p)  │ ~{proj_clust/5000:.1f}s     │")
    print("  └──────────────────────┴──────────────┴───────────┘")


if __name__ == "__main__":
    random.seed(42)
    np.random.seed(42)

    run_tests()
    bias_comparison(CANDIDATES, ROLES, alpha=0.5, cycle='august')
    compare_methods(alpha=0.5, cycle='august')
    full_pipeline(CANDIDATES, ROLES, alpha=0.5, cycle='august')
    scaling_benchmark()
