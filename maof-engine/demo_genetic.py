"""
Maof — Genetic Algorithm Demo
==============================
Demonstrates the self-tuning weight optimizer:
  Default weights (spec) --> Optimized weights (GA) --> Improvement

Usage:
  python demo_genetic.py [--fast]

  --fast  : 8 candidates, 10 generations (quick demo)
  default : 12 candidates, 25 generations (fuller run)
"""

import sys, os, time, argparse
sys.path.insert(0, os.path.dirname(__file__))

from data.synthetic import generate_dataset
from genetic.optimizer import run_genetic_optimizer, default_chromosome


def bar(value: float, width: int = 20) -> str:
    filled = int(value / 100 * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def print_weight_row(label, weights_a, weights_b, fitness, highlight=False):
    marker = " <--" if highlight else ""
    print(f"  {label:<12} | "
          f"ELI5={weights_a['eli5']:.2f}  "
          f"Subj={weights_a['subject']:.2f}  "
          f"Ret={weights_a['retention']:.2f}  "
          f"Imp={weights_a['impact']:.2f}  | "
          f"Tech={weights_b['tech']:.2f}  "
          f"Grow={weights_b['growth']:.2f}  "
          f"Soft={weights_b['soft']:.2f}  "
          f"Cult={weights_b['culture']:.2f}  | "
          f"fitness={fitness:.3f}{marker}")


def run_demo(fast: bool = False):
    n_cand   = 8  if fast else 12
    n_sch    = 4  if fast else 5
    n_co     = 3  if fast else 4
    gens     = 10 if fast else 25
    pop_size = 12 if fast else 20

    print()
    print("=" * 72)
    print("  MAOF — Genetic Algorithm Weight Optimizer")
    print("  Dual Scoring Engine: self-tuning on synthetic placement data")
    print("=" * 72)
    print(f"  Dataset  : {n_cand} candidates | {n_sch} schools | {n_co} companies")
    print(f"  GA params: {pop_size} chromosomes x {gens} generations")
    print()

    print("  Generating synthetic dataset...", end=" ", flush=True)
    candidates, schools, companies = generate_dataset(n_cand, n_sch, n_co)
    print("done")
    print()

    # baseline
    d = default_chromosome()
    default_w = {"eli5": d.w_eli5, "subject": d.w_subject, "retention": d.w_retention, "impact": d.w_impact}
    default_wb = {"tech": d.w_tech, "growth": d.w_growth, "soft": d.w_soft, "culture": d.w_culture}

    print("  Weights: Score A (school fit) | Score B (company fit)")
    print("  " + "-" * 68)
    print("  {:12} | {:35} | {:35} | {}".format(
        "", "-- Score A weights --", "-- Score B weights --", "fitness"))
    print("  " + "-" * 68)
    print_weight_row("Default", default_w, default_wb, d.fitness)
    print()

    print("  Running Genetic Algorithm...")
    print("  " + "-" * 30)
    t0 = time.time()

    result = run_genetic_optimizer(
        candidates, schools, companies,
        population_size=pop_size,
        generations=gens,
        verbose=True,
    )

    elapsed = time.time() - t0
    print("  " + "-" * 30)
    print(f"  Completed in {elapsed:.1f}s")
    print()

    best = result["best_weights"]
    wa   = best["score_a"]
    wb   = best["score_b"]
    bf   = best["fitness"]
    df   = result["default_weights"]["fitness"]
    improvement = result["improvement_abs"]

    print("=" * 72)
    print("  RESULTS")
    print("=" * 72)
    print_weight_row("Default ", default_w, default_wb, df)
    print_weight_row("Optimized", wa, wb, bf, highlight=True)
    print()

    pct = (improvement / df * 100) if df > 0 else 0
    direction = "+" if improvement >= 0 else ""
    print(f"  Fitness improvement : {direction}{improvement:.4f}  ({direction}{pct:.1f}%)")
    print()

    # weight shift summary
    print("  Weight shifts (Default -> Optimized):")
    for name, d_val, o_val in [
        ("ELI5",      d.w_eli5,      wa["eli5"]),
        ("Subject",   d.w_subject,   wa["subject"]),
        ("Retention", d.w_retention, wa["retention"]),
        ("Impact",    d.w_impact,    wa["impact"]),
        ("Tech",      d.w_tech,      wb["tech"]),
        ("Growth",    d.w_growth,    wb["growth"]),
        ("Soft",      d.w_soft,      wb["soft"]),
        ("Culture",   d.w_culture,   wb["culture"]),
    ]:
        delta = o_val - d_val
        arrow = "^" if delta > 0.01 else ("v" if delta < -0.01 else "~")
        print(f"    {name:<10} {d_val:.3f} -> {o_val:.3f}  {arrow} {delta:+.3f}")

    print()
    print("  Learning curve (every 5 generations):")
    history = result["history"]
    for entry in history:
        if entry["generation"] % 5 == 0 or entry["generation"] == 1:
            b = entry["best_fitness"]
            print(f"    gen {entry['generation']:>3}  best={b:.3f}  {bar(b)}")

    print()
    print("=" * 72)
    print("  The GA found weights that better predict placement success.")
    print("  After 50+ real placements, re-run on actual feedback data.")
    print("=" * 72)
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Maof Genetic Optimizer Demo")
    parser.add_argument("--fast", action="store_true", help="Quick run (8 candidates, 10 generations)")
    args = parser.parse_args()
    run_demo(fast=args.fast)
