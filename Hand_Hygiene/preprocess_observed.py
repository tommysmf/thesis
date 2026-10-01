"""Create validated, observation-only tables for the Hand Hygiene dataset.

This script deliberately does not calculate disinfectant consumption.  The raw
load-cell signal is noisy and its unit/calibration is not established yet.
Counterfactual actions and potential outcomes belong in a separate generation
step and must not be mixed with these observed tables.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


XES_NS = {"xes": "http://www.xes-standard.org/"}
TIMESTAMP_RE = re.compile(
    r"^(?P<date>\d{4})[-:]\s?(?P<month>\d{2})[-:]\s?(?P<day>\d{2})"
    r"\s+(?P<time>\d{2}:\d{2}:\d{2}(?:\.\d+)?)"
)


def parse_timestamp(value: str) -> str:
    """Normalize the two timestamp spellings found in the IoT JSONL files."""
    value = value.strip()
    match = TIMESTAMP_RE.match(value)
    if not match:
        raise ValueError(f"Unsupported timestamp: {value!r}")
    normalized = (
        f"{match['date']}-{match['month']}-{match['day']} "
        f"{match['time']}+00:00"
    )
    parsed = datetime.fromisoformat(normalized).astimezone(timezone.utc)
    return parsed.isoformat()


def xes_attributes(element: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    for child in element:
        key = child.attrib.get("key")
        value = child.attrib.get("value")
        if key is not None and value is not None:
            result[key] = value
    return result


def read_xes(path: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    root = ET.parse(path).getroot()
    events: list[dict[str, str]] = []
    actions: list[dict[str, str]] = []

    for trace in root.findall("xes:trace", XES_NS):
        trace_attrs = xes_attributes(trace)
        case_id = trace_attrs.get("concept:name")
        if not case_id:
            raise ValueError(f"Trace without concept:name in {path}")
        has_disturbance = False

        for position, event in enumerate(trace.findall("xes:event", XES_NS)):
            attrs = xes_attributes(event)
            activity = attrs.get("concept:name", "")
            timestamp = attrs.get("time:timestamp")
            if not timestamp:
                raise ValueError(f"Event without timestamp in case {case_id}")
            timestamp = datetime.fromisoformat(timestamp).astimezone(timezone.utc).isoformat()
            row = {
                "case_id": case_id,
                "event_index": str(position),
                "activity": activity,
                "lifecycle_transition": attrs.get("lifecycle:transition", ""),
                "instance_id": attrs.get("concept:instance", ""),
                "timestamp": timestamp,
            }
            events.append(row)
            has_disturbance |= activity.lower() == "disturbance"

        trace_type = "disturbance" if has_disturbance else "basic"
        for row in events:
            if row["case_id"] == case_id:
                row["trace_type"] = trace_type

        by_instance: dict[str, dict[str, str]] = {}
        for row in events:
            if row["case_id"] != case_id or row["activity"].lower() != "hand hygiene":
                continue
            instance = row["instance_id"]
            if not instance:
                continue
            if row["lifecycle_transition"] == "start":
                by_instance[instance] = row
            elif row["lifecycle_transition"] == "complete" and instance in by_instance:
                start = by_instance.pop(instance)
                actions.append(
                    {
                        "case_id": case_id,
                        "trace_type": trace_type,
                        "instance_id": instance,
                        "start_time": start["timestamp"],
                        "end_time": row["timestamp"],
                        "duration_seconds": str(
                            (
                                datetime.fromisoformat(row["timestamp"])
                                - datetime.fromisoformat(start["timestamp"])
                            ).total_seconds()
                        ),
                        "action_observed": "hand_hygiene",
                    }
                )

    return events, actions


def read_iot(paths: Iterable[Path]) -> tuple[list[dict[str, str]], Counter[str]]:
    readings: list[dict[str, str]] = []
    errors: Counter[str] = Counter()
    for path in sorted(paths):
        case_id = path.stem
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                try:
                    raw: dict[str, Any] = json.loads(line)
                    timestamp = parse_timestamp(str(raw.pop("timestamp")))
                    station = str(raw.pop("station"))
                    raw_id = str(raw.pop("id"))
                    row = {
                        "case_id": case_id,
                        "timestamp": timestamp,
                        "station": station,
                        "record_id": raw_id,
                    }
                    row.update({key: str(value) for key, value in raw.items()})
                    readings.append(row)
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                    errors["iot_parse_errors"] += 1
                    raise ValueError(f"{path}:{line_number}: {error}") from error
    return readings, errors


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_quality_report(
    events: list[dict[str, str]],
    actions: list[dict[str, str]],
    readings: list[dict[str, str]],
    iot_errors: Counter[str],
) -> dict[str, Any]:
    cases = sorted({row["case_id"] for row in events})
    stations = Counter(row["station"] for row in readings)
    malformed_load_cell = sum(
        row.get("s23xq_load_cell_weight") in {"", "None"} for row in readings
    )
    return {
        "source": "observed_only",
        "counterfactuals_generated": False,
        "case_count": len(cases),
        "event_count": len(events),
        "completed_hand_hygiene_actions": len(actions),
        "iot_reading_count": len(readings),
        "trace_types": dict(Counter(row["trace_type"] for row in events)),
        "iot_records_by_station": dict(stations),
        "iot_parse_errors": dict(iot_errors),
        "missing_load_cell_values": malformed_load_cell,
        "action_columns": [
            "case_id",
            "trace_type",
            "instance_id",
            "start_time",
            "end_time",
            "duration_seconds",
            "action_observed",
        ],
        "notes": [
            "No ml_used column is produced.",
            "No-action opportunities are not inferred yet.",
            "Potential outcomes must be generated in a separate semi-synthetic step.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path(__file__).parent)
    parser.add_argument("--xes-path", type=Path)
    parser.add_argument("--iot-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "preprocessed")
    args = parser.parse_args()

    xes_paths = [args.xes_path] if args.xes_path else sorted(args.input_dir.glob("*.xes"))
    iot_dir = args.iot_dir if args.iot_dir else args.input_dir / "iot"
    iot_paths = sorted(iot_dir.glob("*.jsonl"))
    if len(xes_paths) != 1:
        raise SystemExit(f"Expected exactly one XES file, found {len(xes_paths)}")
    if not iot_paths:
        raise SystemExit("No IoT JSONL files found")

    events, actions = read_xes(xes_paths[0])
    readings, iot_errors = read_iot(iot_paths)

    event_columns = [
        "case_id",
        "event_index",
        "activity",
        "lifecycle_transition",
        "instance_id",
        "timestamp",
        "trace_type",
    ]
    action_columns = [
        "case_id",
        "trace_type",
        "instance_id",
        "start_time",
        "end_time",
        "duration_seconds",
        "action_observed",
    ]
    reading_columns = ["case_id", "timestamp", "station", "record_id"]
    reading_columns.extend(sorted({key for row in readings for key in row if key not in reading_columns}))

    write_csv(args.output_dir / "observed_events.csv", events, event_columns)
    write_csv(args.output_dir / "observed_hand_hygiene_actions.csv", actions, action_columns)
    write_csv(args.output_dir / "iot_readings.csv", readings, reading_columns)

    report = build_quality_report(events, actions, readings, iot_errors)
    (args.output_dir / "quality_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
