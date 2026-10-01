"""Evaluate small S- and T-learners on the structural benchmark.

This is a deliberately transparent baseline.  It uses the same Ridge base
model for both learners and evaluates against the generated Y(0)/Y(1) values,
which are unavailable in real observational data but known here by design.
Splits are by case_id to prevent opportunities from one trace leaking across
train and test.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import make_pipeline


NUMERIC_FEATURES = [
    "seconds_since_previous_event",
    "disturbance",
    "nfc_status",
    "hygiene_station_presence_proxy",
    "load_cell_observed",
    "historical_policy_propensity",
]
CATEGORICAL_FEATURES = ["trace_type", "previous_activity"]
TARGET = "factual_utility"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def x_matrix(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    return [
        {
            **{key: float(row[key]) for key in NUMERIC_FEATURES},
            **{key: row[key] for key in CATEGORICAL_FEATURES},
        }
        for row in rows
    ]


def utility(row: dict[str, str], action: int) -> float:
    return float(row[f"y{action}_utility"])


def split_by_case(
    rows: list[dict[str, str]], test_fraction: float
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    cases = sorted({row["case_id"] for row in rows})
    test_count = max(1, round(len(cases) * test_fraction))
    test_cases = set(cases[-test_count:])
    train = [row for row in rows if row["case_id"] not in test_cases]
    test = [row for row in rows if row["case_id"] in test_cases]
    return train, test


def make_base_model() -> object:
    return make_pipeline(
        DictVectorizer(sparse=False),
        Ridge(alpha=1.0),
    )


def fit_s_learner(train: list[dict[str, str]]) -> object:
    features = [
        {**features, "action": int(row["action_factual"])}
        for features, row in zip(x_matrix(train), train)
    ]
    model = make_pipeline(DictVectorizer(sparse=False), Ridge(alpha=1.0))
    model.fit(features, [float(row[TARGET]) for row in train])
    return model


def s_predictions(model: object, rows: list[dict[str, str]]) -> tuple[np.ndarray, np.ndarray]:
    context = x_matrix(rows)
    y0 = model.predict([{**row, "action": 0} for row in context])
    y1 = model.predict([{**row, "action": 1} for row in context])
    return y0, y1


def fit_t_learner(train: list[dict[str, str]]) -> tuple[object, object]:
    models = []
    for action in (0, 1):
        subset = [row for row in train if int(row["action_factual"]) == action]
        if not subset:
            raise ValueError(f"Training split has no examples for action {action}")
        model = make_base_model()
        model.fit(x_matrix(subset), [utility(row, action) for row in subset])
        models.append(model)
    return models[0], models[1]


def t_predictions(
    models: tuple[object, object], rows: list[dict[str, str]]
) -> tuple[np.ndarray, np.ndarray]:
    context = x_matrix(rows)
    return models[0].predict(context), models[1].predict(context)


def evaluate(
    name: str,
    y0_hat: np.ndarray,
    y1_hat: np.ndarray,
    rows: list[dict[str, str]],
) -> dict[str, float | str]:
    y0 = np.array([utility(row, 0) for row in rows])
    y1 = np.array([utility(row, 1) for row in rows])
    factual = np.array([utility(row, int(row["action_factual"])) for row in rows])
    predicted_action = (y1_hat > y0_hat).astype(int)
    oracle_action = (y1 > y0).astype(int)
    predicted_policy_value = np.where(predicted_action == 1, y1, y0)
    oracle_value = np.maximum(y0, y1)
    factual_rmse = mean_squared_error(
        factual,
        np.where(np.array([int(row["action_factual"]) for row in rows]) == 1, y1_hat, y0_hat),
    ) ** 0.5
    return {
        "learner": name,
        "test_rows": float(len(rows)),
        "y0_rmse": float(mean_squared_error(y0, y0_hat) ** 0.5),
        "y1_rmse": float(mean_squared_error(y1, y1_hat) ** 0.5),
        "factual_rmse": float(factual_rmse),
        "ite_mae": float(np.mean(np.abs((y1_hat - y0_hat) - (y1 - y0)))),
        "policy_value": float(np.mean(predicted_policy_value)),
        "oracle_policy_value": float(np.mean(oracle_value)),
        "policy_regret": float(np.mean(oracle_value - predicted_policy_value)),
        "oracle_action_accuracy": float(np.mean(predicted_action == oracle_action)),
        "estimated_ate": float(np.mean(y1_hat - y0_hat)),
        "true_ate": float(np.mean(y1 - y0)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).parent
        / "semi_synthetic"
        / "counterfactual_opportunities.csv",
    )
    parser.add_argument("--test-fraction", type=float, default=0.25)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "semi_synthetic" / "learner_results.json",
    )
    args = parser.parse_args()

    rows = read_rows(args.input)
    train, test = split_by_case(rows, args.test_fraction)
    s_model = fit_s_learner(train)
    t_models = fit_t_learner(train)
    s_result = evaluate("S-learner Ridge", *s_predictions(s_model, test), test)
    t_result = evaluate("T-learner Ridge", *t_predictions(t_models, test), test)
    result = {
        "base_model": "sklearn.linear_model.Ridge(alpha=1.0)",
        "split": "case-level; lexicographically last 25% of cases held out",
        "train_cases": sorted({row["case_id"] for row in train}),
        "test_cases": sorted({row["case_id"] for row in test}),
        "train_rows": len(train),
        "test_rows": len(test),
        "results": [s_result, t_result],
        "interpretation": "Metrics use generated potential outcomes and are benchmark metrics, not observational estimates.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
