"""Generate one semi-synthetic cotton candy dataset.

    python generate.py --processed ../datasets/cotton-candy/processed --out output/default
    python generate.py --processed ... --out output/hidden --scenario hidden-confounding
    python generate.py --processed ... --out output/random --set delta=0 --set resamples_per_curve=50

Every --set key=value overrides one knob of ccgen.Config (see ccgen/config.py for the list).
"""
import argparse
import time

from ccgen import Config, load_curves, generate, write
from ccgen.config import SCENARIOS


def parse_value(v):
    for cast in (int, float):
        try:
            return cast(v)
        except ValueError:
            pass
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--processed", required=True, help="folder with runs.csv, sensors.csv, events.csv")
    ap.add_argument("--out", required=True, help="output folder (observed/ and truth/ are created inside)")
    ap.add_argument("--scenario", default="realistic", choices=sorted(SCENARIOS),
                    help="named difficulty setting (see ccgen/config.py); --set overrides on top of it")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="override a Config knob")
    args = ap.parse_args()

    overrides = dict(kv.split("=", 1) for kv in args.set)
    cfg = Config(**{**SCENARIOS[args.scenario], **{k: parse_value(v) for k, v in overrides.items()}})
    t0 = time.time()
    curves = load_curves(args.processed)
    cases, tabs = generate(curves, cfg)
    write(tabs, cfg, args.out)
    c = tabs["cases"]
    print(f"{len(c)} cases ({(c.split == 'train').sum()} train / {(c.split == 'test').sum()} test) "
          f"from {len(curves)} real curves -> {args.out}  [{time.time() - t0:.0f} s]")


if __name__ == "__main__":
    main()
