"""
Genetic Algorithm — Weight Optimizer
מעוף Tech-Lead Israel

מכוונן את משקלות ציון A + ציון B על נתונים סינתטיים.
פותר את בעיית ה-Cold Start לפני שיש נתונים אמיתיים.

כרומוזום = [w_eli5, w_subject, w_retention, w_impact,
             w_tech, w_growth, w_soft, w_culture]
סה"כ 8 משקלות — 4 לציון A, 4 לציון B.

אילוץ: כל קבוצת 4 חייבת לסכום ל-1.0
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import random
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

from models.candidate import Candidate
from models.school import School
from models.company import Company


# --- מבנה כרומוזום ---
@dataclass
class Chromosome:
    # ציון A — חייב לסכום ל-1.0
    w_eli5: float        # ברירת מחדל: 0.35
    w_subject: float     # ברירת מחדל: 0.25
    w_retention: float   # ברירת מחדל: 0.25
    w_impact: float      # ברירת מחדל: 0.15

    # ציון B — חייב לסכום ל-1.0
    w_tech: float        # ברירת מחדל: 0.35
    w_growth: float      # ברירת מחדל: 0.25
    w_soft: float        # ברירת מחדל: 0.25
    w_culture: float     # ברירת מחדל: 0.15

    fitness: float = 0.0

    def to_dict(self) -> dict:
        return {
            "score_a": {
                "eli5": round(self.w_eli5, 3),
                "subject": round(self.w_subject, 3),
                "retention": round(self.w_retention, 3),
                "impact": round(self.w_impact, 3),
            },
            "score_b": {
                "tech": round(self.w_tech, 3),
                "growth": round(self.w_growth, 3),
                "soft": round(self.w_soft, 3),
                "culture": round(self.w_culture, 3),
            },
            "fitness": round(self.fitness, 4),
        }


# --- יצירת כרומוזום אקראי ---
def random_weights_4() -> Tuple[float, float, float, float]:
    """מחזיר 4 משקלות אקראיות שסוכמות ל-1.0"""
    w = [random.random() for _ in range(4)]
    total = sum(w)
    return tuple(x / total for x in w)


def random_chromosome() -> Chromosome:
    a = random_weights_4()
    b = random_weights_4()
    return Chromosome(
        w_eli5=a[0], w_subject=a[1], w_retention=a[2], w_impact=a[3],
        w_tech=b[0], w_growth=b[1], w_soft=b[2], w_culture=b[3],
    )


def default_chromosome() -> Chromosome:
    """ברירת המחדל מהמפרט"""
    return Chromosome(
        w_eli5=0.35, w_subject=0.25, w_retention=0.25, w_impact=0.15,
        w_tech=0.35, w_growth=0.25, w_soft=0.25, w_culture=0.15,
    )


# --- חישוב Fitness ---
def compute_score_a_weighted(candidate: Candidate, school, weights: Chromosome) -> float:
    from scoring.score_a import subject_match_score, retention_score, impact_score
    eli5 = candidate.eli5_score
    subject = subject_match_score(candidate, school)
    retention = retention_score(candidate, school)
    impact = impact_score(school)

    return (
        eli5 * weights.w_eli5 +
        subject * weights.w_subject +
        retention * weights.w_retention +
        impact * weights.w_impact
    )


def compute_score_b_weighted(candidate: Candidate, company, weights: Chromosome) -> float:
    from scoring.score_b import tech_skills_score, growth_potential_score, soft_skills_score, cultural_fit_score
    tech = tech_skills_score(candidate, company)
    growth = growth_potential_score(candidate)
    soft = soft_skills_score(candidate)
    cultural = cultural_fit_score(candidate, company)

    return (
        tech * weights.w_tech +
        growth * weights.w_growth +
        soft * weights.w_soft +
        cultural * weights.w_culture
    )


def evaluate_fitness(
    weights: Chromosome,
    candidates: List[Candidate],
    schools: List,
    companies: List,
) -> float:
    """
    Fitness = סכום ציוני הנפח של כל השיבוצים האפשריים.
    ככל שגבוה יותר — המשקלות טובות יותר.
    """
    from scoring.score_c import calculate_score_c
    from scoring.volume import calculate_volume_score

    total = 0.0
    count = 0

    for candidate in candidates:
        for school in schools:
            for company in companies:
                a = compute_score_a_weighted(candidate, school, weights)
                b = compute_score_b_weighted(candidate, company, weights)
                c = calculate_score_c(a, b, candidate, school, company)
                vol = calculate_volume_score(a, b, c)
                if vol["passes_threshold"]:
                    total += vol["final_score"]
                    count += 1

    return total / max(count, 1)


# --- פעולות גנטיות ---

def normalize_4(a, b, c, d) -> Tuple[float, float, float, float]:
    total = a + b + c + d
    if total == 0:
        return (0.25, 0.25, 0.25, 0.25)
    return (a/total, b/total, c/total, d/total)


def crossover(parent1: Chromosome, parent2: Chromosome) -> Tuple[Chromosome, Chromosome]:
    """Uniform crossover"""
    def mix(v1, v2):
        return v1 if random.random() < 0.5 else v2

    child1_a = normalize_4(
        mix(parent1.w_eli5, parent2.w_eli5),
        mix(parent1.w_subject, parent2.w_subject),
        mix(parent1.w_retention, parent2.w_retention),
        mix(parent1.w_impact, parent2.w_impact),
    )
    child1_b = normalize_4(
        mix(parent1.w_tech, parent2.w_tech),
        mix(parent1.w_growth, parent2.w_growth),
        mix(parent1.w_soft, parent2.w_soft),
        mix(parent1.w_culture, parent2.w_culture),
    )

    child2_a = normalize_4(
        mix(parent2.w_eli5, parent1.w_eli5),
        mix(parent2.w_subject, parent1.w_subject),
        mix(parent2.w_retention, parent1.w_retention),
        mix(parent2.w_impact, parent1.w_impact),
    )
    child2_b = normalize_4(
        mix(parent2.w_tech, parent1.w_tech),
        mix(parent2.w_growth, parent1.w_growth),
        mix(parent2.w_soft, parent1.w_soft),
        mix(parent2.w_culture, parent1.w_culture),
    )

    c1 = Chromosome(*child1_a, *child1_b)
    c2 = Chromosome(*child2_a, *child2_b)
    return c1, c2


def mutate(chromosome: Chromosome, mutation_rate: float = 0.1) -> Chromosome:
    """מוטציה — הוספת רעש גאוסיאני"""
    def mutate_val(v):
        if random.random() < mutation_rate:
            return max(0.01, v + random.gauss(0, 0.05))
        return v

    a = normalize_4(
        mutate_val(chromosome.w_eli5),
        mutate_val(chromosome.w_subject),
        mutate_val(chromosome.w_retention),
        mutate_val(chromosome.w_impact),
    )
    b = normalize_4(
        mutate_val(chromosome.w_tech),
        mutate_val(chromosome.w_growth),
        mutate_val(chromosome.w_soft),
        mutate_val(chromosome.w_culture),
    )
    return Chromosome(*a, *b)


def tournament_select(population: List[Chromosome], k: int = 3) -> Chromosome:
    """Tournament selection"""
    candidates = random.sample(population, min(k, len(population)))
    return max(candidates, key=lambda c: c.fitness)


# --- Main Genetic Algorithm ---

def run_genetic_optimizer(
    candidates: List[Candidate],
    schools: List,
    companies: List,
    population_size: int = 20,
    generations: int = 30,
    mutation_rate: float = 0.1,
    elitism: int = 2,
    verbose: bool = True,
) -> dict:
    """
    מריץ את האלגוריתם הגנטי ומחזיר את המשקלות האופטימליות.
    """

    # אוכלוסיה התחלתית — כולל ברירת המחדל
    population = [default_chromosome()] + [
        random_chromosome() for _ in range(population_size - 1)
    ]

    best_ever = None
    history = []

    for gen in range(generations):
        # חישוב fitness לכל כרומוזום
        for chrom in population:
            chrom.fitness = evaluate_fitness(chrom, candidates, schools, companies)

        # מיון
        population.sort(key=lambda c: c.fitness, reverse=True)
        best = population[0]

        if best_ever is None or best.fitness > best_ever.fitness:
            best_ever = Chromosome(
                best.w_eli5, best.w_subject, best.w_retention, best.w_impact,
                best.w_tech, best.w_growth, best.w_soft, best.w_culture,
                best.fitness
            )

        history.append({
            "generation": gen + 1,
            "best_fitness": round(best.fitness, 4),
            "avg_fitness": round(sum(c.fitness for c in population) / len(population), 4),
        })

        if verbose and (gen + 1) % 5 == 0:
            print(f"  דור {gen+1}/{generations} | best={best.fitness:.3f} | avg={history[-1]['avg_fitness']:.3f}")

        # עלייה לדור הבא
        next_gen = population[:elitism]  # elitism

        while len(next_gen) < population_size:
            p1 = tournament_select(population)
            p2 = tournament_select(population)
            c1, c2 = crossover(p1, p2)
            next_gen.append(mutate(c1, mutation_rate))
            if len(next_gen) < population_size:
                next_gen.append(mutate(c2, mutation_rate))

        population = next_gen

    return {
        "best_weights": best_ever.to_dict(),
        "default_weights": default_chromosome().to_dict(),
        "improvement_abs": round(best_ever.fitness - default_chromosome().fitness, 4),
        "history": history,
        "generations": generations,
        "population_size": population_size,
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    from data.synthetic import generate_dataset

    print("Genetic Algorithm — Weight Optimizer")
    print("=" * 45)

    candidates, schools, companies = generate_dataset(8, 4, 4)
    print(f"Dataset: {len(candidates)} candidates, {len(schools)} schools, {len(companies)} companies")
    print("Running 20 generations...")
    print()

    result = run_genetic_optimizer(
        candidates, schools, companies,
        population_size=15,
        generations=20,
        verbose=True,
    )

    print()
    print("Best weights found:")
    print(f"  Score A: {result['best_weights']['score_a']}")
    print(f"  Score B: {result['best_weights']['score_b']}")
    print(f"  Fitness: {result['best_weights']['fitness']}")
    print(f"  Improvement over default: {result['improvement']}%")
