"""CLI and orchestration for the farm models project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from farm_models.analysis import (
    build_eu_classes,
    build_scores_table,
    build_weights_table,
    build_workbook_tables,
    run_entropy_pipeline,
    write_workbook,
)
from farm_models.clustering import run_hierarchical_clustering
from farm_models.config import DEFAULT_INPUT_FILE, DEFAULT_OUTPUT_DIR, DIMENSIONS
from farm_models.mapping import save_eu_maps
from farm_models.plots import (
    save_cluster_radar_chart,
    save_cluster_scatter_grid,
    save_cluster_validity_summary,
    save_dendrogram,
    save_eu_bar_chart,
    save_eu_scatter_grid,
    save_gap_statistic_plot,
    save_static_sankey,
)


def build_output_layout(output_dir: str | Path) -> dict[str, Path]:
    """Create and return the output directory structure."""
    root = Path(output_dir)
    figures = root / "figures"
    tables = root / "tables"
    cache = root / "cache"
    for path in [root, figures, tables, cache]:
        path.mkdir(parents=True, exist_ok=True)
    return {"root": root, "figures": figures, "tables": tables, "cache": cache}


def write_csv_exports(layout: dict[str, Path], clustering_result: dict[str, object]) -> None:
    """Write clustering audit tables to CSV."""
    clustering_result["assignments"].to_csv(layout["tables"] / "Cluster_Assignments.csv", index=False)
    clustering_result["feature_matrix"].reset_index().rename(columns={"index": "COUNTRY"}).to_csv(
        layout["tables"] / "Clustering_Features_Weighted.csv",
        index=False,
    )
    clustering_result["validity_table"].to_csv(layout["tables"] / "Cluster_Validity_Metrics.csv", index=False)


def build_summary(results: dict[str, dict[str, object]], clustering_result: dict[str, object], warnings: list[str]) -> dict[str, object]:
    """Create a concise machine-readable run summary."""
    weights_table = build_weights_table(results)
    top_weights = (
        weights_table.sort_values(["Dimension", "Weight"], ascending=[True, False])
        .groupby("Dimension")
        .head(3)
        .to_dict(orient="records")
    )
    return {
        "dimensions": DIMENSIONS,
        "top_indicator_weights": top_weights,
        "clustering_feature_space": clustering_result["feature_space"],
        "optimal_k": int(clustering_result["k_opt"]),
        "cluster_sizes": {str(key): int(value) for key, value in clustering_result["cluster_sizes"].items()},
        "warnings": warnings,
    }


def run_pipeline(
    input_path: str | Path,
    output_dir: str | Path,
    skip_maps: bool = False,
    clustering_feature_space: str = "weighted_norm01",
    gap_bootstraps: int = 10,
    random_seed: int = 42,
) -> dict[str, object]:
    """Run the full notebook-equivalent pipeline as a regular project."""
    layout = build_output_layout(output_dir)
    results = run_entropy_pipeline(input_path)
    scores_wide = build_scores_table(results)
    eu_scores, eu_stats = build_eu_classes(scores_wide)
    clustering_result = run_hierarchical_clustering(
        results,
        scores_wide,
        feature_space=clustering_feature_space,
        bootstraps=gap_bootstraps,
        seed=random_seed,
    )
    workbook_tables = build_workbook_tables(results, scores_wide, eu_scores, eu_stats, clustering_result)
    write_workbook(layout["tables"] / "Entropy_Pipeline_Outputs.xlsx", workbook_tables)
    write_csv_exports(layout, clustering_result)

    for dimension in DIMENSIONS:
        save_static_sankey(
            dimension,
            results[dimension]["weights"],
            layout["figures"] / f"Sankey_{dimension}_Static.jpg",
        )

    save_eu_bar_chart(eu_scores, layout["figures"] / "EU_Bar_Chart.jpg")
    save_eu_scatter_grid(eu_scores, layout["figures"] / "EU_Scatter_Triangular_Layout.jpg")
    save_dendrogram(
        clustering_result["linkage_matrix"],
        clustering_result["assignments"]["Code"].tolist(),
        clustering_result["assignments"]["Cluster"].to_numpy(),
        clustering_result["cut_height"],
        clustering_result["k_opt"],
        layout["figures"] / f"Dendrogram_Ward_k{clustering_result['k_opt']}.jpg",
    )
    save_gap_statistic_plot(
        clustering_result["validity_table"],
        clustering_result["k_opt"],
        layout["figures"] / "Gap_Statistic_Plot.jpg",
    )
    save_cluster_validity_summary(
        clustering_result["validity_table"],
        clustering_result["k_opt"],
        layout["figures"] / f"Cluster_Validity_Summary_k{clustering_result['k_opt']}.png",
    )
    save_cluster_scatter_grid(
        clustering_result["assignments"],
        layout["figures"] / f"Scatter_Clusters_k{clustering_result['k_opt']}.jpg",
    )
    save_cluster_radar_chart(
        clustering_result["assignments"],
        layout["figures"] / f"Radar_Clusters_k{clustering_result['k_opt']}.jpg",
    )

    warnings: list[str] = []
    if not skip_maps:
        try:
            save_eu_maps(
                eu_scores,
                layout["figures"] / "EU_Maps_Dimensions_HighQuality.jpg",
                layout["cache"],
            )
        except RuntimeError as exc:
            warnings.append(str(exc))

    summary = build_summary(results, clustering_result, warnings)
    summary["input_file"] = str(Path(input_path).resolve())
    summary["output_dir"] = str(layout["root"].resolve())
    summary_path = layout["root"] / "run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="Run the farm models entropy and clustering pipeline.")
    parser.add_argument("--input", default=DEFAULT_INPUT_FILE, help="Path to the Excel workbook with the three dimension sheets.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help="Directory where tables, figures, and summaries will be written.")
    parser.add_argument(
        "--clustering-feature-space",
        default="weighted_norm01",
        choices=["weighted_norm01", "weighted_probabilities"],
        help="Feature representation used for hierarchical clustering.",
    )
    parser.add_argument("--gap-bootstraps", type=int, default=10, help="Number of bootstrap reference samples for the gap statistic.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for the gap statistic.")
    parser.add_argument("--skip-maps", action="store_true", help="Skip the optional choropleth map figure.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point used by both main.py and python -m farm_models."""
    parser = build_parser()
    args = parser.parse_args(argv)
    summary = run_pipeline(
        input_path=args.input,
        output_dir=args.output,
        skip_maps=args.skip_maps,
        clustering_feature_space=args.clustering_feature_space,
        gap_bootstraps=args.gap_bootstraps,
        random_seed=args.seed,
    )
    print(json.dumps(summary, indent=2))
    return 0
