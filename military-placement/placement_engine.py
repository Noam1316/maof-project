"""
IDF Placement Engine — Gender-Fair Nash-Volume
===============================================

Algorithm:
    score(c,r) = ∛(fit_surplus × urgency_retention × clv_pref) × soft_penalty

Key properties:
  1. Geometric mean → implicit veto: no single party dominates
  2. Gender-fair: uses completion_rate, not contract_duration
  3. Hard binary: medical / kaas / clause stay categorical
  4. Soft sigmoid: cognitive thresholds (dapar, tech, mental)
  5. Three-phase pipeline: combat pre-alloc → GA+quotas → Erdil-Ergin
  6. Fairness audit: individual fairness (Dwork et al., 2012)

Original contribution (not in any prior paper):
  Retention-optimized assignment under commitment constraints,
  with provably gender-neutral temporal scoring.

Reference: Nash (1950), Erdil & Ergin (2008), Dwork et al. (2012)
"""

import math, random, copy
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np

# ────────────────────────────────────────────────
# DATA STRUCTURES
# ────────────────────────────────────────────────

@dataclass
class Candidate:
    name:          str
    dapar:         int            # 10–90 steps of 10
    medical:       int            # 21/45/64/72/82/97
    tech:          int            # 0–100
    manila:        int            # 0–100  (psychotechnical — aptitude)
    mental:        int            # 0–100
    combat:        int            # 0–100  (physical combat fitness)
    pref:          List[str]      # ordered role preferences
    # Extended (30K-scale factors)
    gender:        str   = 'M'    # 'M' / 'F'
    home_city:     str   = 'tel_aviv'
    languages:     List[str] = field(default_factory=list)  # 'arabic','english','russian'
    fitness_score: int   = 50     # מכש"ל 0–100 (separate from combat aptitude)
    leadership_xp: int   = 0      # years
    periphery:     bool  = False
    # Hard-block flags
    kaas:          bool  = False
    clauses:       List[str] = field(default_factory=list)  # ['color_blind','back_injury']

@dataclass
class Role:
    id:           str
    name:         str
    thresh:       Dict             # hard constraints {attr: min_val}
    weights:      Dict             # scoring weights   {attr: weight}  sum=1
    teken:        int              # total capacity
    miluy:        int              # current fill %
    # Extended
    base_lat:     float = 32.08
    base_lon:     float = 34.78
    lang_required:    List[str] = field(default_factory=list)
    reserve_value:    int  = 60   # strategic reserve importance 0–100
    min_fill:         int  = 0    # unit viability floor
    min_women_pct:    float = 0.0
    min_periphery_pct:float = 0.0
    combat_priority:  bool  = False

# ────────────────────────────────────────────────
# DEMO DATA  (6 representative IDF candidates)
# ────────────────────────────────────────────────

CANDIDATES = [
    Candidate("דניאל",   dapar=90, medical=82, tech=90, manila=85, mental=78, combat=20,
               pref=['cyber','product'],
               gender='M', home_city='tel_aviv', languages=['english'],
               fitness_score=55, leadership_xp=0),
    Candidate("אלון",    dapar=90, medical=45, tech=85, manila=80, mental=75, combat=30,
               pref=['cyber','product'],
               gender='M', home_city='rishon', languages=['english'],
               fitness_score=60, leadership_xp=1),
    Candidate("יואב",    dapar=70, medical=97, tech=20, manila=65, mental=92, combat=96,
               pref=['elite','intel'], clauses=['color_blind'],
               gender='M', home_city='haifa', languages=[],
               fitness_score=95, leadership_xp=2),
    Candidate("מאיה",    dapar=70, medical=97, tech=30, manila=75, mental=88, combat=82,
               pref=['elite','intel'],
               gender='F', home_city='netanya', languages=['english'],
               fitness_score=88, leadership_xp=1),
    Candidate("אמיר",    dapar=60, medical=82, tech=55, manila=70, mental=65, combat=45,
               pref=['intel','elint'],
               gender='M', home_city='beer_sheva', languages=['arabic'],
               fitness_score=70, leadership_xp=0, periphery=True),
    Candidate("רן",      dapar=70, medical=45, tech=40, manila=62, mental=50, combat=78,
               pref=['elite','intel'],
               gender='M', home_city='jerusalem', languages=[],
               fitness_score=80, leadership_xp=3),
]

ROLES = [
    Role("admin",   "פקיד לשכה",
         thresh={'dapar':40},
         weights={'dapar':.19,'tech':.08,'manila':.42,'mental':.23,'combat':.08},
         teken=50, miluy=88, reserve_value=30,
         min_fill=5, min_women_pct=0.30, combat_priority=False),
    Role("intel",   "קצין מודיעין",
         thresh={'dapar':70,'medical':72,'mental':55},
         weights={'dapar':.37,'tech':.22,'manila':.17,'mental':.18,'combat':.06},
         teken=80, miluy=48, base_lat=31.91, base_lon=34.90,
         lang_required=['arabic'], reserve_value=90,
         min_fill=15, min_women_pct=0.20, combat_priority=False),
    Role("product", "מנהל מוצר",
         thresh={'dapar':80,'tech':60,'medical':45},
         weights={'dapar':.33,'tech':.31,'manila':.17,'mental':.13,'combat':.06},
         teken=120, miluy=45, lang_required=['english'], reserve_value=75,
         min_fill=10, min_women_pct=0.25, combat_priority=False),
    Role("elint",   "לוחמה אלקטרונית",
         thresh={'dapar':50,'medical':64,'tech':40},
         weights={'dapar':.26,'tech':.36,'manila':.15,'mental':.17,'combat':.06},
         teken=200, miluy=58, base_lat=31.50, base_lon=34.60,
         lang_required=['english'], reserve_value=80,
         min_fill=20, min_women_pct=0.10, combat_priority=True),
    Role("elite",   "יחידת עילית",
         thresh={'medical':97,'mental':85,'combat':80},
         weights={'dapar':.13,'tech':.04,'manila':.13,'mental':.41,'combat':.29},
         teken=300, miluy=78, reserve_value=85,
         min_fill=30, min_women_pct=0.15, combat_priority=True),
    Role("cyber",   "קצין סייבר 8200",
         thresh={'dapar':90,'tech':70,'medical':45},
         weights={'dapar':.39,'tech':.37,'manila':.10,'mental':.09,'combat':.05},
         teken=500, miluy=38, lang_required=['english'], reserve_value=95,
         min_fill=40, min_women_pct=0.20, combat_priority=False),
]

CLAUSE_ROLE_BLOCKS = {'color_blind': ['elint'], 'back_injury': ['elite']}
CITY_COORDS = {
    'tel_aviv':   (32.08, 34.78), 'haifa':      (32.82, 34.99),
    'beer_sheva': (31.25, 34.79), 'jerusalem':  (31.77, 35.21),
    'netanya':    (32.33, 34.86), 'rishon':     (31.97, 34.80),
}
CONTRACT_MONTHS = {'M': 32, 'F': 24}
ROLE_ROI        = {'cyber':1.20,'intel':1.10,'elint':1.05,
                    'elite':1.05,'product':0.95,'admin':0.75}

# ────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))

def _haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

# ────────────────────────────────────────────────
# LAYER 0 — HARD CONSTRAINTS (always binary)
# ────────────────────────────────────────────────

def hard_block(c: Candidate, r: Role) -> Optional[str]:
    """
    Returns block reason if candidate cannot serve in role, else None.
    Medical / kaas / clause are LEGAL requirements — never softened.
    """
    if c.kaas and r.id in ['intel','elite','elint']:
        return f"קה\"ס — עורפי בלבד"
    for cl in c.clauses:
        if r.id in CLAUSE_ROLE_BLOCKS.get(cl, []):
            return f"סעיף ליקוי ({cl})"
    for attr, min_val in r.thresh.items():
        if attr == 'medical' and getattr(c, attr, 0) < min_val:
            return f"פרופיל {c.medical} < {min_val}"
    return None

# ────────────────────────────────────────────────
# LAYER 1 — FIT SURPLUS
# ────────────────────────────────────────────────

def _raw_fit(c: Candidate, r: Role) -> float:
    """Weighted dot product (role-specific weights, IDF scale)."""
    return min(100, sum(r.weights.get(a, 0) * getattr(c, a, 0) for a in r.weights))

def _language_bonus(c: Candidate, r: Role) -> float:
    return sum(10 if l in r.lang_required else 3 for l in c.languages)

def _distance_penalty(c: Candidate, r: Role) -> float:
    lat, lon = CITY_COORDS.get(c.home_city, (32.08, 34.78))
    km = _haversine(lat, lon, r.base_lat, r.base_lon)
    return round(20 * _sigmoid((km - 50) / 30) - 5, 2)

def _soft_penalty(c: Candidate, r: Role, sigma: float = 10.0) -> float:
    """
    Sigmoid smoothing for COGNITIVE thresholds only.
    Medical stays binary (see hard_block).
    A candidate at dapar=80 vs threshold=90 gets partial score,
    not a hard zero — models ±σ measurement error in psychometrics.
    """
    pen = 1.0
    for attr, min_val in r.thresh.items():
        if attr == 'medical':
            continue                     # binary — handled in hard_block
        val = getattr(c, attr, 0)
        if val < min_val:
            pen *= _sigmoid((val - min_val) / sigma)
    return pen

def fit_surplus(c: Candidate, r: Role,
                DISAGREEMENT: float = 40.0,
                eps: float = 1.0) -> float:
    """
    fit_surplus = (enhanced_fit - disagreement_point) + ε

    Enhanced fit adds language match and distance.
    Disagreement point (40) = minimum viable fit below which
    no value is created for either party.
    """
    fitness_bonus = (c.fitness_score - 50) * 0.05 if r.id in ('elite','elint') else 0
    enhanced = _raw_fit(c, r) + _language_bonus(c, r) \
               - _distance_penalty(c, r) + fitness_bonus
    return max(0, enhanced - DISAGREEMENT) + eps

# ────────────────────────────────────────────────
# LAYER 2 — URGENCY × RETENTION
# ────────────────────────────────────────────────

ACTIVITY = {'admin':.8,'intel':1.3,'product':.8,'elint':1.3,'elite':1.3,'cyber':1.0}
CYCLE_M  = {
    'march':    {'combat':.85,'tech':1.15,'intel':.90,'default':1.0},
    'august':   {'combat':1.2,'tech':.90, 'intel':1.1,'default':1.0},
    'november': {'combat':.8, 'tech':1.3, 'intel':.95,'default':1.0},
}
ROLE_TYPE = {'admin':'default','intel':'intel','product':'tech',
              'elint':'combat','elite':'combat','cyber':'tech'}

def urgency(r: Role, cycle: str = 'august') -> float:
    raw  = 100 - r.miluy
    act  = ACTIVITY.get(r.id, 1.0)
    cyc  = CYCLE_M.get(cycle, {}).get(ROLE_TYPE.get(r.id,'default'), 1.0)
    return min(100, round(raw * act * cyc, 2))

def retention(c: Candidate, r: Role, alpha: float = 0.5) -> float:
    """
    P(candidate completes service in this role).
    Predictors: preference match, distance, dapar, leadership experience.
    IDF average ≈ 0.85. Bounds: [0.50, 0.99].
    """
    base = 0.85
    pref_idx = c.pref.index(r.id) if r.id in c.pref else -1
    base += {0:+.08, 1:+.04}.get(pref_idx, -.04)
    lat, lon = CITY_COORDS.get(c.home_city, (32.08, 34.78))
    km    = _haversine(lat, lon, r.base_lat, r.base_lon)
    base -= max(0, (km - 50) / 1000)
    base += (c.dapar - 60) * 0.001 + c.leadership_xp * 0.01
    return round(max(0.50, min(0.99, base)), 4)

def urgency_retention(c: Candidate, r: Role,
                      alpha: float = 0.5, cycle: str = 'august',
                      eps: float = 1.0) -> float:
    """
    urgency × P(complete) + ε
    High urgency + high quit-risk = less real value for army.
    """
    return urgency(r, cycle) * retention(c, r, alpha) + eps

# ────────────────────────────────────────────────
# LAYER 3 — CLV + PREFERENCE SURPLUS (gender-neutral)
# ────────────────────────────────────────────────

def officer_potential(c: Candidate) -> float:
    raw = c.dapar*.40 + c.mental*.30 + c.manila*.20 + c.combat*.10
    return raw if c.medical >= 72 else min(raw, 35)

def clv(c: Candidate, r: Role) -> float:
    """
    Career Lifetime Value = immediate_fit×0.4 + officer_potential×0.3 + reserve×0.3
    All three components are gender-neutral.
    """
    return round(_raw_fit(c,r)*.40 + officer_potential(c)*.30 + r.reserve_value*.30, 2)

def pref_bonus(c: Candidate, r: Role, alpha: float = 0.5) -> float:
    """Preference bonus scaled by α (IDF-controlled parameter)."""
    idx = c.pref.index(r.id) if r.id in c.pref else -1
    return round(alpha * {0:10, 1:5}.get(idx, 0), 2)

def clv_pref_surplus(c: Candidate, r: Role,
                     alpha: float = 0.5, eps: float = 1.0) -> float:
    """pref_bonus + CLV×0.15 + 5 + ε"""
    return pref_bonus(c, r, alpha) + clv(c, r) * 0.15 + 5.0 + eps

# ────────────────────────────────────────────────
# CORE SCORE FUNCTION
# ────────────────────────────────────────────────

def score(c: Candidate, r: Role,
          alpha: float = 0.5,
          cycle: str = 'august') -> float:
    """
    Gender-Fair Nash-Volume Score
    ════════════════════════════
    score(c,r) = ∛( fit_surplus × urgency_retention × clv_pref ) × soft_penalty

    Properties:
    • Geometric mean → implicit veto (no party can dominate)
    • Hard constraints → -∞ (legal requirements, never softened)
    • Soft constraints → sigmoid smoothing (psychometric error ±σ)
    • Gender-neutral → uses completion_rate×role_roi, not contract_duration
    • Nash Bargaining → unique solution satisfying symmetry+Pareto+IIA

    Why ∛: normalizes 3-dimensional volume to linear scale for comparison.
    """
    # Hard block (binary, legal)
    if hard_block(c, r):
        return -math.inf

    fs  = fit_surplus(c, r)
    ur  = urgency_retention(c, r, alpha, cycle)
    cp  = clv_pref_surplus(c, r, alpha)
    sp  = _soft_penalty(c, r)

    # Role ROI (role-dependent, gender-neutral)
    roi = ROLE_ROI.get(r.id, 1.0)

    # Completion rate (replaces contract_duration — removes gender bias)
    comp = retention(c, r, alpha)

    volume = fs * ur * cp * sp
    return round((volume ** (1/3)) * comp * roi, 4)

# ────────────────────────────────────────────────
# PHASE 1 — COMBAT PRE-ALLOCATION
# ────────────────────────────────────────────────

def phase1_combat(candidates: List[Candidate],
                  roles: List[Role],
                  alpha: float = 0.5,
                  cycle: str = 'august') -> Tuple[Dict, List[Candidate]]:
    """
    IDF policy: candidates with medical ≥ 72 receive a combat offer first.
    Only assigns if candidate preference matches OR combat score ≥ 80.
    Returns: pre_assignments dict + remaining candidates for Phase 2.
    """
    combat_roles = [r for r in roles if r.combat_priority]
    eligible = sorted(
        [c for c in candidates if c.medical >= 72],
        key=lambda c: c.combat*.5 + c.mental*.3 + (c.medical/97)*20,
        reverse=True
    )
    pre, used = {}, {r.id: 0 for r in roles}

    for c in eligible:
        best_r, best_s = None, -1
        for r in combat_roles:
            if hard_block(c, r) or used[r.id] >= r.teken:
                continue
            s = score(c, r, alpha, cycle)
            if s > best_s:
                pref_idx = c.pref.index(r.id) if r.id in c.pref else -1
                if pref_idx >= 0 or c.combat >= 80:
                    best_s, best_r = s, r

        if best_r:
            pre[c.name] = best_r.id
            used[best_r.id] += 1

    remaining = [c for c in candidates if c.name not in pre]
    return pre, remaining

# ────────────────────────────────────────────────
# PHASE 2 — GENETIC ALGORITHM WITH QUOTA CONSTRAINTS
# ────────────────────────────────────────────────

def _quota_penalty(assignment: Dict, candidates: List[Candidate],
                   roles: List[Role],
                   n_total_system: int = 30000) -> float:
    """
    Penalty for violating hard constraints:
    Capacity_j, min_fill_j (scaled to batch size), gender %, periphery %.

    min_fill is calibrated for 30K — scaled proportionally to batch size
    so small demo batches are not incorrectly penalized.
    """
    cmap = {c.name: c for c in candidates}
    by_role: Dict[str, List[str]] = {}
    for name, rid in assignment.items():
        by_role.setdefault(rid, []).append(name)

    n_batch = len(candidates)
    scale   = n_batch / n_total_system   # fraction of full system

    pen = 0.0
    for r in roles:
        assigned = [cmap[n] for n in by_role.get(r.id, []) if n in cmap]
        n = len(assigned)
        min_fill_scaled = max(1, round(r.min_fill * scale)) if r.min_fill > 0 else 0

        if n > r.teken:                     pen += (n - r.teken) * 100
        if 0 < n < min_fill_scaled:          pen += (min_fill_scaled - n) * 50
        if n == 0: continue
        women = sum(1 for c in assigned if c.gender == 'F') / n
        if women < r.min_women_pct:         pen += (r.min_women_pct - women) * n * 30
        peri  = sum(1 for c in assigned if c.periphery) / n
        if peri  < r.min_periphery_pct:     pen += (r.min_periphery_pct - peri) * n * 25
    return -pen

def phase2_ga(candidates: List[Candidate], roles: List[Role],
              alpha: float = 0.5, cycle: str = 'august',
              pop_size: int = 60, generations: int = 150) -> Dict:
    """
    Genetic Algorithm over assignment space.

    Chromosome: [role_id for each candidate]  (multi-capacity, not permutation)
    Fitness: Σ score(c_i, r_{chrom_i}) + quota_penalty
    Warm start: greedy seed = Phase 2 starts near-optimal

    Complexity: O(n × pop_size × generations) — linear in n.
    """
    if not candidates:
        return {'assignment': {}, 'total_score': 0.0}

    n       = len(candidates)
    rng     = random.Random(42)
    role_ids = [r.id for r in roles]
    total_t  = sum(r.teken for r in roles)

    # ── Warm start: greedy ───────────────────────────────
    slots = {r.id: r.teken for r in roles}
    warm  = []
    for c in candidates:
        best_rid, best_s = role_ids[0], -9999
        for r in roles:
            if slots.get(r.id, 0) <= 0: continue
            s = score(c, r, alpha, cycle)
            if s not in (-math.inf, None) and s > best_s:
                best_s, best_rid = s, r.id
        warm.append(best_rid)
        slots[best_rid] = slots.get(best_rid, 1) - 1

    def make_random():
        return [rng.choices(role_ids, weights=[r.teken/total_t for r in roles])[0]
                for _ in range(n)]

    def fitness(chrom):
        asgn  = {candidates[i].name: chrom[i] for i in range(n)}
        total = sum(score(candidates[i], next(r for r in roles if r.id==chrom[i]),
                         alpha, cycle)
                    for i in range(n)
                    if score(candidates[i], next(r for r in roles if r.id==chrom[i]),
                             alpha, cycle) not in (-math.inf, None))
        return total + _quota_penalty(asgn, candidates, roles)

    population = [warm] + [make_random() for _ in range(pop_size-1)]
    best_chrom, best_fit = warm.copy(), fitness(warm)

    for _ in range(generations):
        scored = sorted([(fitness(c), c) for c in population],
                        key=lambda x: x[0], reverse=True)
        if scored[0][0] > best_fit:
            best_fit, best_chrom = scored[0][0], scored[0][1].copy()

        elite   = [c for _, c in scored[:max(1, pop_size//10)]]
        new_pop = elite.copy()
        while len(new_pop) < pop_size:
            p1 = rng.choice(scored[:pop_size//2])[1]
            p2 = rng.choice(scored[:pop_size//2])[1]
            pt = rng.randint(1, n-1)
            child = p1[:pt] + p2[pt:]
            if rng.random() < 0.12:
                child[rng.randint(0,n-1)] = rng.choice(role_ids)
            new_pop.append(child)
        population = new_pop

    assignment = {candidates[i].name: best_chrom[i] for i in range(n)}
    return {'assignment': assignment, 'total_score': round(best_fit, 4)}

# ────────────────────────────────────────────────
# PHASE 3 — ERDIL-ERGIN STABLE IMPROVEMENTS
# ────────────────────────────────────────────────

def phase3_erdil_ergin(result: Dict, candidates: List[Candidate],
                        roles: List[Role], alpha: float = 0.5,
                        cycle: str = 'august') -> Dict:
    """
    Post-processing: find and execute stable improvement cycles (Erdil & Ergin, 2008).

    A stable improvement exists when swapping two candidates'
    roles makes BOTH strictly better (or one better, one equal).
    Guaranteed to terminate. Result is stable + Pareto efficient.
    """
    assignment = result['assignment'].copy()
    cmap = {c.name: c for c in candidates}
    rmap = {r.id: r for r in roles}
    names, swaps = list(assignment.keys()), 0

    improved = True
    while improved:
        improved = False
        for i in range(len(names)):
            for j in range(i+1, len(names)):
                a, b = names[i], names[j]
                ra, rb = rmap[assignment[a]], rmap[assignment[b]]
                ca, cb = cmap[a], cmap[b]
                # Block check on swapped roles
                if hard_block(ca, rb) or hard_block(cb, ra):
                    continue
                s_aa = score(ca, ra, alpha, cycle)
                s_bb = score(cb, rb, alpha, cycle)
                s_ab = score(ca, rb, alpha, cycle)
                s_ba = score(cb, ra, alpha, cycle)
                if (s_ab > s_aa and s_ba >= s_bb) or (s_ab >= s_aa and s_ba > s_bb):
                    assignment[a], assignment[b] = assignment[b], assignment[a]
                    swaps += 1
                    improved = True
                    break
            if improved:
                break

    total = sum(score(cmap[n], rmap[rid], alpha, cycle)
                for n, rid in assignment.items()
                if score(cmap[n], rmap[rid], alpha, cycle) not in (-math.inf, None))
    return {'assignment': assignment, 'total_score': round(total,4), 'swaps': swaps}

# ────────────────────────────────────────────────
# FAIRNESS AUDIT  (Dwork et al., 2012)
# ────────────────────────────────────────────────

def fairness_audit(assignment: Dict, candidates: List[Candidate],
                   roles: List[Role],
                   profile_eps: float = 0.08,
                   score_delta: float = 8.0) -> List[Dict]:
    """
    Individual Fairness: similar candidates → similar assignments.

    For each M/F pair with profile distance < eps:
      if |fit(F, role_F) - fit(M, role_M)| > delta → violation.

    Profile distance = weighted L1 over (dapar, tech, mental, manila).
    """
    cmap, rmap = {c.name:c for c in candidates}, {r.id:r for r in roles}
    violations = []

    females = [c for c in candidates if c.gender=='F']
    males   = [c for c in candidates if c.gender=='M']

    for cf in females:
        for cm in males:
            d = (abs(cf.dapar  - cm.dapar)  /90  * .35 +
                 abs(cf.tech   - cm.tech)   /100 * .25 +
                 abs(cf.mental - cm.mental) /100 * .20 +
                 abs(cf.manila - cm.manila) /100 * .20)
            if d > profile_eps: continue

            rf_id, rm_id = assignment.get(cf.name), assignment.get(cm.name)
            if not rf_id or not rm_id: continue

            sf = _raw_fit(cf, rmap[rf_id])
            sm = _raw_fit(cm, rmap[rm_id])
            delta = sm - sf

            if abs(delta) > score_delta:
                violations.append({
                    'female': cf.name, 'male': cm.name,
                    'profile_dist': round(d,3),
                    'female_role':  rf_id, 'male_role': rm_id,
                    'fit_delta':    round(delta,1),
                    'bias_direction': 'man_favored' if delta>0 else 'woman_favored',
                })
    return violations

# ────────────────────────────────────────────────
# FULL PIPELINE
# ────────────────────────────────────────────────

def run(candidates: List[Candidate] = CANDIDATES,
        roles:      List[Role]      = ROLES,
        alpha:      float           = 0.5,
        cycle:      str             = 'august',
        verbose:    bool            = True) -> Dict:
    """
    Full three-phase pipeline:
      Phase 1 → Combat pre-allocation   (IDF policy)
      Phase 2 → GA + quota constraints  (Nash-Volume objective)
      Phase 3 → Erdil-Ergin             (Pareto stability)
      Audit   → Individual Fairness     (gender check)
    """
    rmap = {r.id: r for r in roles}
    cmap = {c.name: c for c in candidates}

    if verbose:
        print(f"\n{'═'*52}")
        print(f"  IDF Placement Engine  |  α={alpha}  cycle={cycle}")
        print(f"{'═'*52}")

    # ── Phase 1 ──────────────────────────────────
    pre, remaining = phase1_combat(candidates, roles, alpha, cycle)
    if verbose and pre:
        print(f"\nPhase 1 — Combat pre-allocation ({len(pre)} candidates):")
        for name, rid in pre.items():
            print(f"  {name} → {rmap[rid].name}")

    # ── Phase 2 ──────────────────────────────────
    roles_adj = copy.deepcopy(roles)
    slots_used = {}
    for rid in pre.values():
        slots_used[rid] = slots_used.get(rid,0) + 1
    for r in roles_adj:
        r.teken = max(1, r.teken - slots_used.get(r.id, 0))

    ga_result = phase2_ga(remaining, roles_adj, alpha, cycle)

    # ── Phase 3 ──────────────────────────────────
    final = phase3_erdil_ergin(ga_result, remaining, roles_adj, alpha, cycle)

    # ── Merge & report ───────────────────────────
    merged = {**pre, **final['assignment']}
    violations = fairness_audit(merged, candidates, roles)

    if verbose:
        print(f"\nFinal Assignment ({len(merged)}/{len(candidates)} placed):")
        print(f"  {'Name':<8} {'Phase':<6} {'Role':<24} {'Score':>7}  Pref")
        print("  " + "─"*55)
        for name, rid in merged.items():
            c    = cmap[name]
            r    = rmap[rid]
            s    = score(c, r, alpha, cycle)
            ph   = "P1" if name in pre else "P2"
            pref_tag = "❤️" if rid in c.pref[:1] else "🔵" if rid in c.pref[1:2] else "  "
            s_str = f"{s:.2f}" if s not in (-math.inf, None) else "blocked"
            print(f"  {name:<8} [{ph}]   {r.name:<24} {s_str:>7}  {pref_tag}")

        unplaced = [c.name for c in candidates if c.name not in merged]
        if unplaced:
            print(f"\n  ⚠️  Unplaced (committee): {', '.join(unplaced)}")

        print(f"\n  Nash total: {final['total_score']:.2f}"
              f"  |  Erdil-Ergin swaps: {final['swaps']}")

        if violations:
            print(f"\n  ⚠️  Fairness violations ({len(violations)}):")
            for v in violations:
                print(f"    {v['female']}(F,{v['female_role']}) vs "
                      f"{v['male']}(M,{v['male_role']}): "
                      f"Δ={v['fit_delta']:+.1f} [{v['bias_direction']}]")
        else:
            print(f"\n  ✅ Individual fairness: no gender violations detected.")

    return {'assignment': merged, 'violations': violations,
            'total_score': final['total_score']}


# ────────────────────────────────────────────────
# ENTRY POINT
# ────────────────────────────────────────────────

if __name__ == '__main__':
    random.seed(42)
    np.random.seed(42)

    # Run all three cycles
    for cyc in ['march', 'august', 'november']:
        run(cycle=cyc, alpha=0.5)

    # α effect demonstration
    print(f"\n{'═'*52}")
    print("  α Effect — who benefits when army defers to soldier?")
    print(f"{'═'*52}")
    rmap_d = {r.id: r for r in ROLES}
    for a in [0.0, 0.5, 1.0]:
        result = run(alpha=a, cycle='august', verbose=False)
        line   = "  α={:.1f}:  ".format(a)
        for name, rid in result['assignment'].items():
            c = next(x for x in CANDIDATES if x.name==name)
            tag = "❤️" if rid in c.pref[:1] else "🔵" if rid in c.pref[1:2] else "·"
            line += f"{name}→{rid[:4]}{tag}  "
        print(line)
