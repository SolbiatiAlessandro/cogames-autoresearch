"""Quick analysis of results.tsv — run with: uv run analysis.py"""

import csv
import sys

def main():
    try:
        with open("results.tsv") as f:
            reader = csv.DictReader(f, delimiter="\t")
            rows = list(reader)
    except FileNotFoundError:
        print("No results.tsv found. Run some experiments first.")
        sys.exit(1)

    if not rows:
        print("results.tsv is empty.")
        return

    print(f"Total experiments: {len(rows)}")
    print(f"  Kept:      {sum(1 for r in rows if r['status'] == 'keep')}")
    print(f"  Discarded: {sum(1 for r in rows if r['status'] == 'discard')}")
    print(f"  Crashed:   {sum(1 for r in rows if r['status'] == 'crash')}")

    kept = [r for r in rows if r["status"] == "keep"]
    if kept:
        scores = [float(r["composite_score"]) for r in kept]
        print(f"\nBest composite_score: {max(scores):.6f}")
        print(f"Current (latest keep): {scores[-1]:.6f}")
        print(f"\nKept experiments (chronological):")
        for r in kept:
            print(f"  {r['commit']}  {float(r['composite_score']):.6f}  {r['description']}")

    # Top improvements
    if len(kept) > 1:
        deltas = []
        for i in range(1, len(kept)):
            prev = float(kept[i-1]["composite_score"])
            curr = float(kept[i]["composite_score"])
            deltas.append((curr - prev, kept[i]))
        deltas.sort(reverse=True)
        print(f"\nTop improvements:")
        for delta, r in deltas[:5]:
            print(f"  +{delta:.6f}  {r['commit']}  {r['description']}")


if __name__ == "__main__":
    main()
