"""Data loading, classification, and workbook assembly."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from farm_models.config import DIMENSIONS, EU27, WORKBOOK_SHEET_DESCRIPTIONS
from farm_models.entropy import process_dimension_sheet


def load_dimension_sheets(input_path: str | Path) -> dict[str, pd.DataFrame]:
    """Load the expected workbook sheets into memory."""
    xls = pd.ExcelFile(input_path)
    missing_sheets = [dimension for dimension in DIMENSIONS if dimension not in xls.sheet_names]
    if missing_sheets:
        raise ValueError(f"Workbook is missing required sheets: {missing_sheets}")
    return {dimension: pd.read_excel(input_path, sheet_name=dimension) for dimension in DIMENSIONS}


def run_entropy_pipeline(input_path: str | Path) -> dict[str, dict[str, object]]:
    """Process the workbook and return the results for each dimension."""
    sheets = load_dimension_sheets(input_path)
    return {dimension: process_dimension_sheet(df, dimension) for dimension, df in sheets.items()}


def prefixed_block(countries: pd.Series, block: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Prefix dimension names so tables can be merged safely across pillars."""
    return pd.concat([countries.rename("COUNTRY"), block.add_prefix(f"{dimension}::")], axis=1)


def merge_dimension_blocks(results: dict[str, dict[str, object]], block_key: str) -> pd.DataFrame:
    """Merge one table type across all dimensions into a single wide table."""
    merged = prefixed_block(results[DIMENSIONS[0]]["countries"], results[DIMENSIONS[0]][block_key], DIMENSIONS[0])
    for dimension in DIMENSIONS[1:]:
        merged = merged.merge(
            prefixed_block(results[dimension]["countries"], results[dimension][block_key], dimension),
            on="COUNTRY",
            how="outer",
        )
    return merged


def build_weights_table(results: dict[str, dict[str, object]]) -> pd.DataFrame:
    """Assemble all entropy weights in tidy format."""
    frames = []
    for dimension in DIMENSIONS:
        columns = results[dimension]["columns"]
        weights = results[dimension]["weights"]
        frames.append(
            pd.DataFrame(
                {
                    "Dimension": dimension,
                    "Indicator": columns,
                    "Weight": [float(weights[column]) for column in columns],
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def build_scores_table(results: dict[str, dict[str, object]]) -> pd.DataFrame:
    """Assemble one row per country with the three composite scores."""
    scores = pd.DataFrame({"COUNTRY": results[DIMENSIONS[0]]["countries"]})
    for dimension in DIMENSIONS:
        scores = scores.merge(
            pd.DataFrame(
                {
                    "COUNTRY": results[dimension]["countries"],
                    f"{dimension} Score": results[dimension]["score"],
                }
            ),
            on="COUNTRY",
            how="inner",
        )
    return scores


def build_sankey_links(weights_table: pd.DataFrame) -> pd.DataFrame:
    """Create indicator-to-dimension links for plotting or export."""
    links = weights_table.rename(columns={"Indicator": "Source", "Dimension": "Target", "Weight": "Value"}).copy()
    links["Type"] = "Indicator -> Dimension"
    return links[["Source", "Target", "Value", "Type"]]


def classify_mu_sigma(value: float, mean_value: float, std_value: float) -> str | float:
    """Assign a country to a four-band class based on mean ± standard deviation."""
    if pd.isna(value):
        return np.nan
    if value > mean_value + std_value:
        return "High"
    if value > mean_value:
        return "Medium-high"
    if value > mean_value - std_value:
        return "Medium-low"
    return "Low"


def build_eu_classes(scores_wide: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Filter to EU27 and compute the class labels and summary statistics."""
    eu_scores = scores_wide[scores_wide["COUNTRY"].isin(EU27)].copy()
    stats_rows = []
    for dimension in DIMENSIONS:
        score_column = f"{dimension} Score"
        class_column = f"{dimension} Class"
        mean_value = eu_scores[score_column].mean()
        std_value = eu_scores[score_column].std(ddof=1)
        eu_scores[class_column] = eu_scores[score_column].apply(
            lambda value: classify_mu_sigma(value, mean_value, std_value)
        )
        stats_rows.append({"Dimension": dimension, "Mean (mu)": mean_value, "Std (sigma)": std_value})
    eu_stats = pd.DataFrame(stats_rows)
    return eu_scores, eu_stats


def build_readme_sheet() -> pd.DataFrame:
    """Turn the workbook descriptions into a two-column sheet."""
    return pd.DataFrame(
        [{"Sheet": sheet_name, "Description": description} for sheet_name, description in WORKBOOK_SHEET_DESCRIPTIONS.items()]
    )


def build_workbook_tables(
    results: dict[str, dict[str, object]],
    scores_wide: pd.DataFrame,
    eu_scores: pd.DataFrame,
    eu_stats: pd.DataFrame,
    clustering_result: dict[str, object],
) -> dict[str, pd.DataFrame]:
    """Collect all workbook outputs in sheet order."""
    weights_table = build_weights_table(results)
    return {
        "README": build_readme_sheet(),
        "Data": merge_dimension_blocks(results, "raw"),
        "Oriented": merge_dimension_blocks(results, "oriented"),
        "Probabilities": merge_dimension_blocks(results, "probabilities"),
        "Norm01": merge_dimension_blocks(results, "norm01"),
        "Entropy_Weights": weights_table,
        "Scores_Wide": scores_wide,
        "Sankey_Links": build_sankey_links(weights_table),
        "EU_SD_Classes": eu_scores,
        "EU_SD_Stats": eu_stats,
        "Cluster_Validity": clustering_result["validity_table"],
        "Cluster_Assignments": clustering_result["assignments"],
    }


def write_workbook(output_path: str | Path, workbook_tables: dict[str, pd.DataFrame]) -> None:
    """Write the assembled workbook with the openpyxl engine."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, table in workbook_tables.items():
            table.to_excel(writer, sheet_name=sheet_name, index=False)
