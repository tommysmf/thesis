"""Validate a benchmark: realism (adapter checks), headroom, confounding, knob sweeps and scenarios.

    python validate.py --adapter cotton_candy --data ../datasets/cotton-candy/processed [--quick]

Writes validation_report_<adapter>.md (or ..._quick.md with --quick) next to this script.
"""
import argparse
import os

from adapters import get_adapter
from presbench.validation import report
from presbench import twostage, twostage_validation

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--quick", action="store_true", help="one seed, fewer resamples, no sweeps")
    args = ap.parse_args()
    adapter = get_adapter(args.adapter)
    cases = adapter.load(args.data)
    make = twostage_validation.report if isinstance(adapter, twostage.TwoStageAdapter) else report
    text = "\n".join(make(adapter, cases, quick=args.quick))
    print(text)
    name = f"validation_report_{adapter.name}{'_quick' if args.quick else ''}.md"
    with open(os.path.join(HERE, name), "w") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()
