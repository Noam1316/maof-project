import sys, math
sys.path.insert(0, '.')
from scoring.volume import calculate_volume_score, soft_gate

def old(a, b, c):
    if a < 60 or b < 60 or c < 60:
        return 0.0
    vol = (a-60)*(b-60)*(c-60)
    vs = min(100, (vol**(1/3))/40*100)
    return round(vs*0.5 + a*0.25 + b*0.25, 2)

cases = [
    (59.9, 90, 90),
    (60.1, 90, 90),
    (55.0, 90, 90),
    (65.0, 65, 65),
    (75.0, 75, 75),
    (80.0, 80, 80),
    (95.0, 95, 95),
    (54.0, 90, 90),
]

print("Case                       Old        New      Gate")
print("-" * 58)
for a, b, c in cases:
    r = calculate_volume_score(a, b, c)
    g = round(soft_gate(a) * soft_gate(b) * soft_gate(c), 3)
    new_score = r["final_score"]
    print(f"  A={a:<5} B={b} C={c}    {old(a,b,c):<10} {new_score:<10} {g}")
