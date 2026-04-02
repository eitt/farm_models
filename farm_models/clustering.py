"""Hierarchical clustering and validity diagnostics."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
from numpy.random import default_rng
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score

from farm_models.config import DIMENSIONS


def country_code(label: str) -> str:
    """Extract the two-letter country code used in the dataset."""
    match = re.search(r"\(([A-Z]{2})\)", str(label))
    if match:
        return match.group(1)
    return str(label)[:2].upper()


def build_feature_matrix(
    results: dict[str, dict[str, object]],
    scores_wide: pd.DataFrame,
    feature_space: str = "weighted_norm01",
) -> pd.DataFrame:
    """Build the feature matrix used for clustering."""
    blocks = []
    for dimension in DIMENSIONS:
        if feature_space == "weighted_norm01":
            block = results[dimension]["norm01"].mul(results[dimension]["weights"], axis=1)
        elif feature_space == "weighted_probabilities":
            scale = np.sqrt(results[dimension]["weights"] / len(DIMENSIONS))
            block = results[dimension]["probabilities"].mul(scale, axis=1)
        else:
            raise ValueError("feature_space must be 'weighted_norm01' or 'weighted_probabilities'")
        blocks.append(block.add_prefix(f"{dimension}::"))
    feature_matrix = pd.concat(blocks, axis=1)
    feature_matrix.index = scores_wide["COUNTRY"]
    return feature_matrix


def within_ss(matrix: np.ndarray, labels: np.ndarray) -> float:
    """Calculate total within-cluster sum of squares."""
    sum_squares = 0.0
    for label in np.unique(labels):
        cluster_matrix = matrix[labels == label]
        if cluster_matrix.shape[0] <= 1:
            continue
        centroid = cluster_matrix.mean(axis=0, keepdims=True)
        sum_squares += ((cluster_matrix - centroid) ** 2).sum()
    return float(sum_squares)


def gap_statistic(
    matrix: np.ndarray,
    k_values: list[int],
    bootstraps: int = 10,
    seed: int = 42,
) -> tuple[dict[int, float], dict[int, float], dict[int, float]]:
    """Compute the gap statistic and its standard errors."""
    rng = default_rng(seed)
    n_rows, n_cols = matrix.shape
    mins, maxs = matrix.min(axis=0), matrix.max(axis=0)
    gaps: dict[int, float] = {}
    gap_ses: dict[int, float] = {}
    within_scores: dict[int, float] = {}

    for k_value in k_values:
        labels = AgglomerativeClustering(n_clusters=k_value, linkage="ward").fit_predict(matrix)
        observed_within = within_ss(matrix, labels)
        within_scores[k_value] = observed_within

        log_reference = []
        for _ in range(bootstraps):
            reference = rng.random((n_rows, n_cols)) * (maxs - mins)[None, :] + mins[None, :]
            reference_labels = AgglomerativeClustering(n_clusters=k_value, linkage="ward").fit_predict(reference)
            reference_within = within_ss(reference, reference_labels)
            if reference_within > 0:
                log_reference.append(np.log(reference_within))

        if not log_reference or observed_within <= 0:
            gaps[k_value] = float("-inf")
            gap_ses[k_value] = 0.0
            continue

        gap_mean = float(np.mean(log_reference))
        gap_std = float(np.std(log_reference, ddof=1)) if len(log_reference) > 1 else 0.0
        gaps[k_value] = gap_mean - float(np.log(observed_within))
        gap_ses[k_value] = gap_std * np.sqrt(1.0 + 1.0 / len(log_reference))

    return gaps, gap_ses, within_scores


def build_validity_table(
    feature_matrix: pd.DataFrame,
    max_k: int = 7,
    bootstraps: int = 10,
    seed: int = 42,
) -> pd.DataFrame:
    """Compute clustering diagnostics across candidate values of k."""
    matrix = feature_matrix.to_numpy()
    if matrix.shape[0] < 3:
        raise ValueError("At least three observations are required for clustering diagnostics.")

    max_candidate = min(max_k, matrix.shape[0] - 1)
    k_values = list(range(2, max_candidate + 1))
    gaps, gap_ses, within_scores = gap_statistic(matrix, k_values, bootstraps=bootstraps, seed=seed)

    rows = []
    for k_value in k_values:
        labels = AgglomerativeClustering(n_clusters=k_value, linkage="ward").fit_predict(matrix)
        rows.append(
            {
                "k": k_value,
                "Gap": gaps.get(k_value, np.nan),
                "Gap_SE": gap_ses.get(k_value, np.nan),
                "Silhouette": silhouette_score(matrix, labels),
                "Calinski_Harabasz": calinski_harabasz_score(matrix, labels),
                "Davies_Bouldin": davies_bouldin_score(matrix, labels),
                "Within_SS": within_scores.get(k_value, np.nan),
            }
        )
    return pd.DataFrame(rows)


def choose_optimal_k(validity_table: pd.DataFrame) -> int:
    """Apply the gap-statistic 1-SE rule and fall back to the smallest valid k."""
    if validity_table.empty:
        return 2
    validity_table = validity_table.sort_values("k").reset_index(drop=True)
    for current, following in zip(validity_table.itertuples(index=False), validity_table.iloc[1:].itertuples(index=False)):
        if current.Gap >= (following.Gap - following.Gap_SE):
            return int(current.k)
    return int(validity_table.iloc[0]["k"])


def threshold_for_k(linkage_matrix: np.ndarray, k_value: int) -> float:
    """Compute the cut height that yields the desired number of clusters."""
    heights = np.sort(linkage_matrix[:, 2])
    if k_value <= 1:
        return float(heights.max() + 0.1)
    cut_index = len(heights) - k_value
    return float(0.5 * (heights[cut_index] + heights[min(cut_index + 1, len(heights) - 1)]))


def run_hierarchical_clustering(
    results: dict[str, dict[str, object]],
    scores_wide: pd.DataFrame,
    feature_space: str = "weighted_norm01",
    max_k: int = 7,
    bootstraps: int = 10,
    seed: int = 42,
) -> dict[str, object]:
    """Run Ward clustering and return diagnostics, assignments, and profiles."""
    feature_matrix = build_feature_matrix(results, scores_wide, feature_space=feature_space)
    validity_table = build_validity_table(feature_matrix, max_k=max_k, bootstraps=bootstraps, seed=seed)
    optimal_k = choose_optimal_k(validity_table)
    linkage_matrix = linkage(feature_matrix.to_numpy(), method="ward")
    cluster_labels = fcluster(linkage_matrix, optimal_k, criterion="maxclust")

    assignments = scores_wide.copy()
    assignments["Cluster"] = cluster_labels
    assignments["Code"] = assignments["COUNTRY"].apply(country_code)
    profiles = assignments.groupby("Cluster")[[f"{dimension} Score" for dimension in DIMENSIONS]].mean()
    cluster_sizes = assignments["Cluster"].value_counts().sort_index().to_dict()

    return {
        "feature_space": feature_space,
        "feature_matrix": feature_matrix,
        "validity_table": validity_table,
        "linkage_matrix": linkage_matrix,
        "k_opt": optimal_k,
        "cut_height": threshold_for_k(linkage_matrix, optimal_k),
        "assignments": assignments,
        "profiles": profiles,
        "cluster_sizes": cluster_sizes,
    }
