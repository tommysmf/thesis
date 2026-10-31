"""Generate one semi-synthetic benchmark dataset.

    python generate.py --adapter cotton_candy --data ../datasets/cotton-candy/processed --out output/cc
    python generate.py --adapter cotton_candy --data ... --out output/cc_hidden --scenario hidden-confounding
    python generate.py --adapter cotton_candy --data ... --out output/cc_random --set delta=0
    python generate.py --adapter cotton_candy_joint --data ... --out output/cc_joint   # start and stop together

Every --set key=value overrides one knob: a core knob (presbench/config.py) or an adapter knob (its Params).
"""
import argparse
import time

from adapters import get_adapter
from presbench import make_settings, generate, write
from presbench import twostage


def parse_value(v):
    for cast in (int, float):
        try:
            return cast(v)
        except ValueError:
            pass
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True, help="adapter name: a folder in adapters/")
    ap.add_argument("--data", required=True, help="the dataset folder the adapter reads")
    ap.add_argument("--out", required=True, help="output folder (observed/ and truth/ are created inside)")
    ap.add_argument("--scenario", default="realistic", help="named setting defined by the adapter")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="override a knob")
    args = ap.parse_args()

    adapter = get_adapter(args.adapter)
    overrides = {k: parse_value(v) for k, v in (kv.split("=", 1) for kv in args.set)}
    settings = make_settings(adapter, args.scenario, **overrides)
    t0 = time.time()
    cases = adapter.load(args.data)
    if isinstance(adapter, twostage.TwoStageAdapter):     # two linked decisions per case
        _, tables = twostage.generate(adapter, cases, settings)
        twostage.write(tables, settings, adapter, args.out)
    else:
        _, tables = generate(adapter, cases, settings)
        write(tables, settings, adapter, args.out)
    c = tables["cases"]
    print(f"{len(c)} cases ({(c.split == 'train').sum()} train / {(c.split == 'test').sum()} test) "
          f"from {len(cases)} real cases -> {args.out}  [{time.time() - t0:.0f} s]")


if __name__ == "__main__":
    main()
