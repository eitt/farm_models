"""Entropy weighting helpers."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from farm_models.config import COST_COLUMNS, SCHEMA


def orient_columns(raw_df: pd.DataFrame, cost_set: set[str]) -> pd.DataFrame:
    """Flip the sign of cost indicators so higher means better everywhere."""
    oriented = raw_df.astype(float).copy()
    for column in oriented.columns:
        if column in cost_set:
            oriented[column] = -oriented[column]
    return oriented


def minmax01_by_column(oriented_df: pd.DataFrame) -> pd.DataFrame:
    """Apply min-max scaling column by column to the oriented matrix."""
    mins = oriented_df.min(axis=0)
    maxs = oriented_df.max(axis=0)
    ranges = (maxs - mins).replace(0.0, np.nan)
    normalized = (oriented_df - mins) / ranges
    return normalized.fillna(0.0).clip(lower=0.0, upper=1.0)


def compute_probabilities(oriented_df: pd.DataFrame) -> pd.DataFrame:
    """Compute column-sum probabilities used by Shannon entropy."""
    col_sums = oriented_df.sum(axis=0).replace(0.0, np.nan)
    probabilities = oriented_df.div(col_sums, axis=1)
    probabilities = probabilities.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return probabilities.clip(lower=0.0).abs()


def entropy_weights_from_probs(probabilities: pd.DataFrame) -> pd.Series:
    """Convert Shannon entropy into normalized indicator weights."""
    col_sums = probabilities.sum(axis=0)
    valid = col_sums[col_sums > 0].index
    if len(valid) == 0:
        return pd.Series(1.0 / probabilities.shape[1], index=probabilities.columns, dtype=float)

    n_rows = probabilities.shape[0]
    k_constant = 1.0 / math.log(n_rows) if n_rows > 1 else 0.0
    with np.errstate(divide="ignore", invalid="ignore"):
        log_prob = np.log(probabilities[valid].replace(0, np.nan))
    entropy_term = (probabilities[valid] * log_prob).fillna(0.0)
    entropy = -k_constant * entropy_term.sum(axis=0)
    diversity = 1.0 - entropy
    weights_valid = diversity / diversity.sum() if diversity.sum() > 0 else pd.Series(
        1.0 / len(valid), index=valid, dtype=float
    )

    weights = pd.Series(0.0, index=probabilities.columns, dtype=float)
    weights.loc[weights_valid.index] = weights_valid
    return weights / weights.sum() if weights.sum() > 0 else pd.Series(
        1.0 / len(weights), index=weights.index, dtype=float
    )


def process_dimension_sheet(df: pd.DataFrame, dimension: str) -> dict[str, object]:
    """Run the full entropy pipeline for a single dimension sheet."""
    country_column = df.columns[0]
    countries = df[country_column].astype(str).str.strip()
    required_columns = SCHEMA[dimension]
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"[{dimension}] Missing columns: {missing}")

    raw = df[required_columns].astype(float)
    cost_set = set(COST_COLUMNS.get(dimension, []))
    oriented = orient_columns(raw, cost_set)
    probabilities = compute_probabilities(oriented)
    weights = entropy_weights_from_probs(probabilities)
    norm01 = minmax01_by_column(oriented)
    weighted_components = norm01.mul(weights, axis=1)
    score = weighted_components.sum(axis=1)

    return {
        "countries": countries,
        "raw": raw,
        "oriented": oriented,
        "probabilities": probabilities,
        "norm01": norm01,
        "weights": weights,
        "weighted_components": weighted_components,
        "score": score,
        "columns": required_columns,
    }
