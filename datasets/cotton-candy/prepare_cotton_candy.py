"""
Prepare the Cotton Candy dataset (Zenodo 10.5281/zenodo.17226615) for semi-synthetic work.

Reads every candy run ("Cottonbot - Run with Data Collection ...") from the raw XES-YAML traces
and writes three tables to ./processed/:

  runs.csv     one row per candy: settings (wait/cook/cooldown time), maintenance counters,
               measured outcomes (weight, sizes, pressures), key timestamps, sensor values at
               the moment spinning starts, and data-quality flags
  sensors.csv  the sensor time series of every run (one row per poll, ~every 2 s):
               head/ambient infrared temperature, internal and environment temperature +
               humidity, plug power + current; time is in seconds since the machine was turned on
  events.csv   the process event log (activity completions), without the sensor-polling activities

Run from anywhere:  python prepare_cotton_candy.py
"""
import glob
import os
import re
from datetime import datetime, timedelta, timezone

import pandas as pd
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "processed")
LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
LOCAL_TZ = timezone(timedelta(hours=2))          # sensor timestamps without offset are local (CEST)
POLLING = {"Get the Environment Data", "Get the Plug Data", "Wait 2 seconds"}
RUN_PREFIX = "Cottonbot - Run with Data Collection"


def parse_time(value):
    """Event and sensor timestamps come in several formats; return an aware datetime or None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=LOCAL_TZ)
    s = str(value).strip().strip("'")
    if not s or s == "0":
        return None
    s = re.sub(r"(\.\d{6})\d+", r"\1", s)        # nanoseconds -> microseconds
    s = re.sub(r"\.(\d{1,5})(?=$|[+-])", lambda m: "." + m.group(1).ljust(6, "0"), s)  # ".77" -> ".770000" (Python < 3.11)
    s = re.sub(r" ([+-]\d\d:\d\d)$", r"\1", s)    # "... +02:00" -> "...+02:00"
    try:
        dt = datetime.fromisoformat(s.replace(" ", "T", 1))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=LOCAL_TZ)


def to_float(v):
    try:
        return float(str(v).strip("'"))
    except (TypeError, ValueError):
        return None


def iter_points(stream, path=()):
    """Walk the nested stream:datastream structure; yield (path_of_stream_names, id, value, timestamp)."""
    name = None
    for item in stream or []:
        if not isinstance(item, dict):
            continue
        if "stream:name" in item:
            name = item["stream:name"]
        elif "stream:datastream" in item:
            yield from iter_points(item["stream:datastream"], path + ((name,) if name else ()))
        elif "stream:point" in item:
            p = item["stream:point"]
            yield path + ((name,) if name else ()), p.get("stream:id"), p.get("stream:value"), p.get("stream:timestamp")


def sensor_column(path, sid):
    """Map a stream point to a column name."""
    if sid == "head":
        return "ir_head"
    if sid == "ambient":
        return "ir_ambient"
    if sid in ("power", "current"):
        return sid
    if sid in ("temperature", "humidity"):
        if "internal" in path:
            return "internal_" + ("temp" if sid == "temperature" else "hum")
        if "environment" in path:
            return "env_" + ("temp" if sid == "temperature" else "hum")
    return None


def parse_run(path):
    docs = list(yaml.load_all(open(path, encoding="utf-8"), Loader=LOADER))
    trace = docs[0]["log"]["trace"]
    run = {"file": os.path.relpath(path, ROOT).replace("\\", "/"),
           "batch": os.path.relpath(path, ROOT).replace("\\", "/").split("/")[-2],
           "instance": trace.get("concept:name"), "uuid": trace.get("cpee:instance"),
           "variant": (trace.get("cpee:name") or "").replace(RUN_PREFIX, "").strip() or "standard"}
    data, sensors, events, measures = {}, [], [], {}
    for d in docs[1:]:
        ev = (d or {}).get("event") or {}
        name = str(ev.get("concept:name", "")).strip().strip("'\"")
        trans = ev.get("cpee:lifecycle:transition")
        ts = parse_time(ev.get("time:timestamp"))
        if trans == "dataelements/change":
            for de in ev.get("data") or []:
                if isinstance(de, dict) and "name" in de:
                    data[de["name"]] = de.get("value")
        elif trans == "stream/data":
            row = {}
            for spath, sid, val, sts in iter_points(ev.get("stream:datastream")):
                col = sensor_column(spath, sid)
                if col:
                    row[col] = to_float(val)
                    row["ts"] = parse_time(sts) or ts
                elif sid in ("pos1", "pos2", "pos3"):
                    measures[f"{('pressure' if 'pressures' in spath else 'size')}_{sid}"] = to_float(val)
            if any(k != "ts" for k in row):
                sensors.append(row)
        elif trans == "activity/done" and name and name not in POLLING:
            events.append({"activity": name, "time": ts})
        if trans in ("activity/calling", "activity/done") and name in ("Create Cotton Candy", "Turn the Machine On"):
            run[f"{'create' if name.startswith('Create') else 'machine_on'}_{trans.split('/')[1]}"] = ts
    # settings and outcomes (last value of each data element)
    for k in ["batch_number", "batch_since_maintenance", "iteration_since_maintenance", "stick", "wait_time",
              "cook_time", "cooldown_time", "cold_start_wait", "sugar_amount", "stick_weight", "weight",
              "total_time", "handover_time", "radius", "height", "quality_score"]:
        run[k] = to_float(data.get(k))
    for key in ("sizes", "max_pressures"):
        v = data.get(key)
        if isinstance(v, dict):
            for pos in ("pos1", "pos2", "pos3"):
                run[f"{'size' if key == 'sizes' else 'max_pressure'}_{pos}_data"] = to_float(v.get(pos))
    run.update(measures)
    return run, sensors, events


def main():
    os.makedirs(OUT, exist_ok=True)
    files = sorted(glob.glob(os.path.join(ROOT, "**", "*.xes.yaml"), recursive=True))
    runs, sensor_rows, event_rows = [], [], []
    for i, f in enumerate(files):
        with open(f, encoding="utf-8") as fh:
            head = fh.read(3000)
        names = re.findall(r"cpee:name: (.+)", head)          # first match is the __NOTSPECIFIED__ default
        if not any(n.strip().startswith(RUN_PREFIX) for n in names):
            continue                                          # sub-processes (robot moves etc.) and batch parents
        run, sensors, events = parse_run(f)
        t0 = run.get("machine_on_done") or (sensors[0]["ts"] if sensors else None)
        for s in sensors:
            s["instance"] = run["instance"]
            s["t"] = (s["ts"] - t0).total_seconds() if (t0 and s.get("ts")) else None
        for e in events:
            e["instance"] = run["instance"]
        # sensor values when spinning starts (the end of the heating/wait phase)
        cs = run.get("create_calling")
        before = [s for s in sensors if s.get("ts") and cs and s["ts"] <= cs]
        for col in ("ir_head", "internal_temp", "power"):
            vals = [s[col] for s in before if s.get(col) is not None]
            run[f"{col}_at_create"] = vals[-1] if vals else None
        heads = [s["ir_head"] for s in sensors if s.get("ir_head") is not None]
        run["ir_head_max"] = max(heads) if heads else None
        run["n_sensor_polls"] = len(sensors)
        run["sec_on_to_create"] = (cs - t0).total_seconds() if (cs and t0) else None
        runs.append(run)
        sensor_rows += sensors
        event_rows += events
        if len(runs) % 25 == 0:
            print(f"  parsed {len(runs)} runs ({i + 1}/{len(files)} files)")

    runs = pd.DataFrame(runs)
    # some runs are stored twice (e.g. the nested batch-3/batch-4 folder): keep the first copy only
    n_before = len(runs)
    runs = runs.drop_duplicates("uuid", keep="first").reset_index(drop=True)
    print(f"dropped {n_before - len(runs)} duplicate runs")
    # data-quality flags (weight is net of stick? stick_weight is stored separately; see README notes)
    runs["weight_valid"] = runs["weight"].between(1, 60)
    runs["settings_valid"] = (runs["wait_time"] >= 0) & (runs["cook_time"] > 0)
    runs["has_sensor_series"] = runs["n_sensor_polls"] > 20
    sensors = pd.DataFrame(sensor_rows).drop_duplicates(["instance", "ts"])
    events = pd.DataFrame(event_rows).drop_duplicates(["instance", "time", "activity"])
    for df in (runs, sensors, events):
        for c in df.columns:
            if df[c].dtype == object and df[c].map(lambda v: isinstance(v, datetime)).any():
                df[c] = pd.to_datetime(df[c], utc=True)
    runs.to_csv(os.path.join(OUT, "runs.csv"), index=False)
    sensors[["instance", "ts", "t", "ir_head", "ir_ambient", "internal_temp", "internal_hum", "env_temp",
             "env_hum", "power", "current"]].to_csv(os.path.join(OUT, "sensors.csv"), index=False)
    events[["instance", "time", "activity"]].to_csv(os.path.join(OUT, "events.csv"), index=False)
    print(f"\nruns: {len(runs)}  sensor polls: {len(sensors)}  events: {len(events)}  -> {OUT}")


if __name__ == "__main__":
    main()
