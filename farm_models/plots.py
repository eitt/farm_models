"""Plotting helpers for the farm models pipeline."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.transforms import Bbox
from scipy.cluster.hierarchy import dendrogram

from farm_models.clustering import country_code
from farm_models.config import A4_WIDTH_INCHES, CLASS_ORDER, CLUSTER_COLORS, DIMENSIONS, DPI_SETTING, SD_COLORS, SCHEMA


def ensure_parent_dir(output_path: str | Path) -> Path:
    """Create the parent directory for a plot if needed."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def build_cluster_gradient(num_colors: int) -> list[tuple[float, float, float, float] | str]:
    """Create a green-to-blue palette that matches the cluster visual language."""
    if num_colors <= 1:
        return [CLUSTER_COLORS[0]]
    cmap = LinearSegmentedColormap.from_list(
        "cluster_gradient",
        [CLUSTER_COLORS[0], CLUSTER_COLORS[1]],
    )
    return [cmap(position) for position in np.linspace(0.15, 0.85, num_colors)]


def build_dendrogram_color_maps(
    linkage_matrix: np.ndarray,
    cluster_labels: list[int] | np.ndarray,
    above_color: str = "#999999",
) -> tuple[dict[int, str], dict[int, str]]:
    """Map each dendrogram branch to the project cluster palette."""
    cluster_array = np.asarray(cluster_labels, dtype=int)
    cluster_color_lookup = {
        cluster_id: CLUSTER_COLORS[(cluster_id - 1) % len(CLUSTER_COLORS)]
        for cluster_id in sorted(np.unique(cluster_array))
    }

    n_leaves = len(cluster_array)
    node_clusters = {leaf_id: {int(cluster_array[leaf_id])} for leaf_id in range(n_leaves)}
    node_colors: dict[int, str] = {}

    for merge_index, (left_child, right_child, _distance, _count) in enumerate(linkage_matrix):
        node_id = n_leaves + merge_index
        merged_clusters = node_clusters[int(left_child)] | node_clusters[int(right_child)]
        node_clusters[node_id] = merged_clusters
        node_colors[node_id] = (
            cluster_color_lookup[next(iter(merged_clusters))]
            if len(merged_clusters) == 1
            else above_color
        )

    return node_colors, cluster_color_lookup


def candidate_label_offsets(index: int) -> list[tuple[int, int]]:
    """Return a rotated list of candidate offsets for label placement."""
    base_offsets = [
        (10, 10),
        (12, -10),
        (-12, 10),
        (-12, -10),
        (0, 14),
        (0, -14),
        (16, 0),
        (-16, 0),
        (18, 12),
        (-18, 12),
        (18, -12),
        (-18, -12),
        (22, 6),
        (-22, 6),
        (22, -6),
        (-22, -6),
        (0, 20),
        (0, -20),
    ]
    rotation = index % len(base_offsets)
    return base_offsets[rotation:] + base_offsets[:rotation]


def bbox_penalty(candidate_bbox, existing_bboxes: list, axes_bbox) -> float:
    """Score a candidate label box based on overlaps and leaving the axes."""
    overlap_area = 0.0
    for existing_bbox in existing_bboxes:
        if candidate_bbox.overlaps(existing_bbox):
            x_overlap = max(0.0, min(candidate_bbox.x1, existing_bbox.x1) - max(candidate_bbox.x0, existing_bbox.x0))
            y_overlap = max(0.0, min(candidate_bbox.y1, existing_bbox.y1) - max(candidate_bbox.y0, existing_bbox.y0))
            overlap_area += x_overlap * y_overlap

    outside_penalty = 0.0
    outside_penalty += max(axes_bbox.x0 - candidate_bbox.x0, 0.0)
    outside_penalty += max(candidate_bbox.x1 - axes_bbox.x1, 0.0)
    outside_penalty += max(axes_bbox.y0 - candidate_bbox.y0, 0.0)
    outside_penalty += max(candidate_bbox.y1 - axes_bbox.y1, 0.0)
    return overlap_area + 250.0 * outside_penalty


def estimate_text_bbox(ax, x_value: float, y_value: float, label: str, dx: int, dy: int, font_size: float, ha: str, va: str):
    """Estimate a label bounding box in display coordinates without forcing a redraw."""
    point_x, point_y = ax.transData.transform((x_value, y_value))
    scale = ax.figure.dpi / 72.0
    text_width = max(18.0, len(str(label)) * font_size * 0.62 * scale)
    text_height = font_size * 1.55 * scale
    pad = 4.0
    anchor_x = point_x + dx * scale
    anchor_y = point_y + dy * scale

    if ha == "left":
        x0, x1 = anchor_x - pad, anchor_x + text_width + pad
    else:
        x0, x1 = anchor_x - text_width - pad, anchor_x + pad

    if va == "bottom":
        y0, y1 = anchor_y - pad, anchor_y + text_height + pad
    else:
        y0, y1 = anchor_y - text_height - pad, anchor_y + pad

    return Bbox.from_extents(x0, y0, x1, y1)


def add_offset_labels(
    ax,
    x_values: pd.Series | np.ndarray | list[float],
    y_values: pd.Series | np.ndarray | list[float],
    labels: pd.Series | np.ndarray | list[str],
    colors: pd.Series | np.ndarray | list[str],
    font_size: float = 8.0,
) -> None:
    """Place labels away from their points and connect them with dotted leader lines."""
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    axes_bbox = ax.get_window_extent(renderer=renderer).padded(-8.0)
    x_values = list(x_values)
    y_values = list(y_values)
    labels = list(labels)
    colors = list(colors)

    existing_bboxes: list = []
    placement_order = sorted(range(len(labels)), key=lambda idx: (y_values[idx], x_values[idx]), reverse=True)

    for label_index in placement_order:
        x_value = x_values[label_index]
        y_value = y_values[label_index]
        label = labels[label_index]
        color = colors[label_index]
        best_choice = None

        for dx, dy in candidate_label_offsets(label_index):
            ha = "left" if dx >= 0 else "right"
            va = "bottom" if dy >= 0 else "top"
            candidate_bbox = estimate_text_bbox(ax, x_value, y_value, label, dx, dy, font_size, ha, va).expanded(1.06, 1.14)
            penalty = bbox_penalty(candidate_bbox, existing_bboxes, axes_bbox) + 0.35 * (abs(dx) + abs(dy))

            if best_choice is None or penalty < best_choice[0]:
                best_choice = (penalty, dx, dy, candidate_bbox)
            if penalty <= 1.0:
                break

        _, dx, dy, candidate_bbox = best_choice
        connection_radius = 0.22 if dx >= 0 else -0.22
        ax.annotate(
            label,
            xy=(x_value, y_value),
            xytext=(dx, dy),
            textcoords="offset points",
            ha="left" if dx >= 0 else "right",
            va="bottom" if dy >= 0 else "top",
            fontsize=font_size,
            fontweight="bold",
            color=color,
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.78),
            arrowprops=dict(
                arrowstyle="-",
                lw=0.7,
                linestyle=(0, (1.5, 1.8)),
                color=color,
                alpha=0.75,
                connectionstyle=f"arc3,rad={connection_radius}",
                shrinkA=2,
                shrinkB=4,
            ),
            zorder=5,
            annotation_clip=True,
        )
        existing_bboxes.append(candidate_bbox)


def add_quadrant_annotations(ax, x_name: str, y_name: str) -> None:
    """Place quadrant annotations inside the axes to avoid panel overlap."""
    labels = quadrant_labels(x_name, y_name)
    positions = {
        "TL": (0.03, 0.97, "left", "top", "#555555"),
        "TR": (0.97, 0.97, "right", "top", "#1a9850"),
        "BL": (0.03, 0.03, "left", "bottom", "#d73027"),
        "BR": (0.97, 0.03, "right", "bottom", "#555555"),
    }
    for key, (x_pos, y_pos, ha, va, color) in positions.items():
        ax.text(
            x_pos,
            y_pos,
            labels[key],
            transform=ax.transAxes,
            ha=ha,
            va=va,
            fontsize=6.5,
            color=color,
            fontweight="bold" if key in {"TR", "BL"} else None,
            fontstyle="italic" if key in {"TL", "BR"} else None,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.72, boxstyle="round,pad=0.18"),
            zorder=6,
        )


def save_static_sankey(dimension: str, weights: pd.Series, output_path: str | Path) -> None:
    """Draw a lightweight Sankey-style plot using Matplotlib primitives."""
    output_path = ensure_parent_dir(output_path)
    indicators = list(SCHEMA[dimension])
    values = [float(weights[indicator]) for indicator in indicators]
    total_weight = sum(values)
    palette = build_cluster_gradient(len(indicators))

    fig, ax = plt.subplots(figsize=(A4_WIDTH_INCHES, A4_WIDTH_INCHES * 0.6))
    ax.axis("off")

    left_x, right_x = 0.08, 0.92
    width_gap = right_x - left_x
    y_top, y_bottom = 0.9, 0.1
    height_available = y_top - y_bottom
    spacing = 0.02
    total_spacing = spacing * max(len(indicators) - 1, 0)
    scale_factor = (height_available - total_spacing) / total_weight

    ax.add_patch(
        mpatches.FancyBboxPatch(
            (right_x - 0.02, y_bottom),
            0.04,
            height_available,
            boxstyle="round,pad=0.01",
            ec=CLUSTER_COLORS[1],
            fc=CLUSTER_COLORS[1],
            lw=1,
        )
    )
    ax.text(right_x + 0.03, 0.5, f"{dimension}\nDimension", ha="left", va="center", fontsize=12)

    left_cursor = y_bottom
    right_cursor = y_bottom
    for index, (indicator, value) in enumerate(zip(indicators, values)):
        block_height = value * scale_factor
        right_height = (value / total_weight) * height_available
        color = palette[index]

        ax.add_patch(
            mpatches.Rectangle(
                (left_x - 0.02, left_cursor),
                0.02,
                block_height,
                ec="white",
                fc=color,
            )
        )
        ax.text(
            left_x - 0.03,
            left_cursor + block_height / 2.0,
            f"{indicator}\n({value:.3f})",
            ha="right",
            va="center",
            fontsize=9,
            color="#333333",
        )

        path_data = [
            (mpath.Path.MOVETO, (left_x, left_cursor)),
            (mpath.Path.CURVE4, (left_x + width_gap * 0.5, left_cursor)),
            (mpath.Path.CURVE4, (right_x - width_gap * 0.5, right_cursor)),
            (mpath.Path.LINETO, (right_x, right_cursor)),
            (mpath.Path.LINETO, (right_x, right_cursor + right_height)),
            (mpath.Path.CURVE4, (right_x - width_gap * 0.5, right_cursor + right_height)),
            (mpath.Path.CURVE4, (left_x + width_gap * 0.5, left_cursor + block_height)),
            (mpath.Path.LINETO, (left_x, left_cursor + block_height)),
            (mpath.Path.CLOSEPOLY, (left_x, left_cursor)),
        ]
        codes, vertices = zip(*path_data)
        patch = mpatches.PathPatch(mpath.Path(vertices, codes), facecolor=color, alpha=0.4, edgecolor="none")
        ax.add_patch(patch)

        left_cursor += block_height + spacing
        right_cursor += right_height

    plt.savefig(output_path, dpi=DPI_SETTING, bbox_inches="tight", format="jpg")
    plt.close(fig)


def save_eu_bar_chart(eu_scores: pd.DataFrame, output_path: str | Path) -> None:
    """Create the three-panel EU bar chart colored by mean ± sigma class."""
    output_path = ensure_parent_dir(output_path)
    score_columns = [f"{dimension} Score" for dimension in DIMENSIONS]

    fig, axes = plt.subplots(1, 3, figsize=(19, 9.5))
    plt.subplots_adjust(left=0.08, right=0.99, top=0.90, bottom=0.14, wspace=0.42)
    for ax, score_column in zip(axes, score_columns):
        class_column = score_column.replace(" Score", " Class")
        ordered = eu_scores.sort_values(score_column, ascending=False).reset_index(drop=True)
        colors = [SD_COLORS.get(label, "#cccccc") for label in ordered[class_column]]
        ax.barh(ordered["COUNTRY"], ordered[score_column], color=colors, edgecolor="white", linewidth=0.5)
        ax.invert_yaxis()
        ax.set_title(score_column.replace(" Score", ""), fontsize=15, weight="bold", pad=10)
        ax.set_xlabel("Composite score", fontsize=11)
        ax.tick_params(axis="y", labelsize=8.5, pad=2)
        ax.tick_params(axis="x", labelsize=10)
        ax.grid(axis="x", linestyle=":", alpha=0.25)
        ax.set_axisbelow(True)

    legend_handles = [mpatches.Patch(color=SD_COLORS[label], label=label) for label in CLASS_ORDER]
    fig.legend(legend_handles, CLASS_ORDER, loc="lower center", bbox_to_anchor=(0.5, 0.03), ncol=4, frameon=False, fontsize=11)
    plt.savefig(output_path, dpi=DPI_SETTING, bbox_inches="tight", format="jpg")
    plt.close(fig)


def worse_class(class_one: str, class_two: str) -> str:
    """Color pairwise plots by the weaker of the two dimension classes."""
    rank = {label: index for index, label in enumerate(CLASS_ORDER)}
    if pd.isna(class_one):
        return class_two
    if pd.isna(class_two):
        return class_one
    return class_one if rank[class_one] <= rank[class_two] else class_two


def quadrant_labels(x_name: str, y_name: str) -> dict[str, str]:
    """Generate readable quadrant labels for scatter panels."""
    x_short = x_name.replace(" Score", "").replace("Economic", "Econ").replace("Environmental", "Env").replace("Social", "Soc")
    y_short = y_name.replace(" Score", "").replace("Economic", "Econ").replace("Environmental", "Env").replace("Social", "Soc")
    return {
        "TR": "Synergy\n(High-High)",
        "TL": f"Trade-off\n(High {y_short})",
        "BR": f"Trade-off\n(High {x_short})",
        "BL": "Deficit\n(Low-Low)",
    }


def save_eu_scatter_grid(eu_scores: pd.DataFrame, output_path: str | Path) -> None:
    """Create the 2x2 pairwise scatter layout used in the notebook."""
    output_path = ensure_parent_dir(output_path)
    pairs = [
        (0, 0, "Economic Score", "Environmental Score"),
        (0, 1, "Economic Score", "Social Score"),
        (1, 0, "Environmental Score", "Social Score"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    plt.subplots_adjust(top=0.95, bottom=0.08, left=0.07, right=0.98, wspace=0.34, hspace=0.34)

    mean_lookup = {
        score_column: (eu_scores[score_column].mean(), eu_scores[score_column].std(ddof=1))
        for score_column in [f"{dimension} Score" for dimension in DIMENSIONS]
    }
    class_lookup = {f"{dimension} Score": f"{dimension} Class" for dimension in DIMENSIONS}

    for row_index, col_index, x_column, y_column in pairs:
        ax = axes[row_index, col_index]
        ordered = eu_scores.sort_values([x_column, y_column]).reset_index(drop=True)
        pair_classes = [worse_class(a, b) for a, b in zip(ordered[class_lookup[x_column]], ordered[class_lookup[y_column]])]
        colors = [SD_COLORS.get(label, "#cccccc") for label in pair_classes]

        ax.scatter(
            ordered[x_column],
            ordered[y_column],
            s=60,
            alpha=0.9,
            edgecolors="white",
            linewidth=0.5,
            c=colors,
            zorder=3,
        )
        codes = ordered["COUNTRY"].apply(country_code)
        add_offset_labels(ax, ordered[x_column], ordered[y_column], codes, colors, font_size=8.0)

        mean_x = mean_lookup[x_column][0]
        mean_y = mean_lookup[y_column][0]
        ax.axvline(mean_x, ls="--", lw=0.8, color="#444444", alpha=0.6, zorder=1)
        ax.axhline(mean_y, ls="--", lw=0.8, color="#444444", alpha=0.6, zorder=1)
        ax.text(
            mean_x,
            0.985,
            f"mu={mean_x:.2f}",
            transform=ax.get_xaxis_transform(),
            fontsize=8,
            color="#444444",
            ha="center",
            va="top",
            fontweight="bold",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.72, boxstyle="round,pad=0.15"),
        )
        ax.text(
            0.985,
            mean_y,
            f"mu={mean_y:.2f}",
            transform=ax.get_yaxis_transform(),
            fontsize=8,
            color="#444444",
            ha="right",
            va="center",
            fontweight="bold",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.72, boxstyle="round,pad=0.15"),
        )

        add_quadrant_annotations(ax, x_column, y_column)

        ax.set_xlim(-0.05, 1.05)
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlabel(x_column.replace(" Score", ""), fontsize=12, weight="bold")
        ax.set_ylabel(y_column.replace(" Score", ""), fontsize=12, weight="bold")
        ax.grid(True, ls=":", alpha=0.3)
        ax.tick_params(labelsize=11)

    ax_desc = axes[1, 1]
    ax_desc.axis("off")
    legend_elements = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label=label,
            markerfacecolor=color,
            markersize=10,
            markeredgecolor="gray",
        )
        for label, color in reversed(list(SD_COLORS.items()))
    ]
    ax_desc.legend(
        handles=legend_elements,
        loc="center",
        bbox_to_anchor=(0.5, 0.8),
        title="Performance Tiers\n(Based on mean: mu +/- sigma)",
        title_fontsize=12,
        fontsize=11,
        frameon=False,
        alignment="left",
    )
    ax_desc.text(
        0.5,
        0.05,
        "Quadrant definitions:\n"
        "Synergy: score > mu in both dimensions.\n"
        "Trade-off: one dimension is above mu while the other is not.\n"
        "Deficit: score <= mu in both dimensions.\n\n"
        "Dashed lines represent the EU mean (mu).",
        transform=ax_desc.transAxes,
        ha="center",
        va="bottom",
        fontsize=10,
        color="#444444",
        bbox=dict(facecolor="#f9f9f9", edgecolor="#dddddd", boxstyle="round,pad=1"),
    )

    plt.savefig(output_path, dpi=DPI_SETTING, bbox_inches="tight", format="jpg")
    plt.close(fig)


def save_dendrogram(
    linkage_matrix: np.ndarray,
    labels: list[str],
    cluster_labels: list[int] | np.ndarray,
    cut_height: float,
    optimal_k: int,
    output_path: str | Path,
) -> None:
    """Save the Ward dendrogram with the chosen cut height."""
    output_path = ensure_parent_dir(output_path)
    above_color = "#999999"
    node_colors, cluster_color_lookup = build_dendrogram_color_maps(
        linkage_matrix,
        cluster_labels,
        above_color=above_color,
    )
    fig = plt.figure(figsize=(10, 6))
    dendro = dendrogram(
        linkage_matrix,
        labels=labels,
        leaf_rotation=0,
        leaf_font_size=10,
        color_threshold=cut_height,
        above_threshold_color=above_color,
        link_color_func=lambda node_id: node_colors.get(node_id, above_color),
    )
    ax = plt.gca()
    cluster_array = np.asarray(cluster_labels, dtype=int)
    for tick_label, leaf_index in zip(ax.get_xmajorticklabels(), dendro["leaves"]):
        cluster_id = int(cluster_array[leaf_index])
        tick_label.set_color(cluster_color_lookup[cluster_id])
        tick_label.set_fontweight("bold")
    plt.axhline(cut_height, c="r", ls="--", lw=1, label=f"Cut height (k={optimal_k})")
    plt.ylabel("Distance (Ward)")
    plt.title(f"Hierarchy of EU agriculture (optimal k={optimal_k})", fontsize=12)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=DPI_SETTING, bbox_inches="tight", format="jpg")
    plt.close(fig)


def save_gap_statistic_plot(validity_table: pd.DataFrame, optimal_k: int, output_path: str | Path) -> None:
    """Plot the gap statistic with 1-SE error bars."""
    output_path = ensure_parent_dir(output_path)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(
        validity_table["k"],
        validity_table["Gap"],
        yerr=validity_table["Gap_SE"],
        fmt="-o",
        color="navy",
        ecolor="gray",
        capsize=5,
        capthick=1.5,
        elinewidth=1.5,
        markersize=8,
        linewidth=2,
        label="Gap statistic",
    )
    optimal_row = validity_table.loc[validity_table["k"] == optimal_k].iloc[0]
    ax.plot(optimal_k, optimal_row["Gap"], "ro", markersize=12, label=f"Optimal k={optimal_k}")
    ax.annotate(
        f"Optimal k={optimal_k}",
        (optimal_k, optimal_row["Gap"]),
        xytext=(optimal_k + 0.4, optimal_row["Gap"] - 0.05),
        arrowprops=dict(arrowstyle="->", color="black"),
        fontsize=11,
        fontweight="bold",
    )
    ax.set_xlabel("Number of clusters (k)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Gap value", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(output_path, dpi=DPI_SETTING, bbox_inches="tight", format="jpg")
    plt.close(fig)


def save_cluster_validity_summary(validity_table: pd.DataFrame, optimal_k: int, output_path: str | Path) -> None:
    """Summarize the main clustering diagnostics in one figure."""
    output_path = ensure_parent_dir(output_path)
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    metric_specs = [
        ("Gap", "Gap statistic", True),
        ("Silhouette", "Silhouette", True),
        ("Calinski_Harabasz", "Calinski-Harabasz", True),
        ("Davies_Bouldin", "Davies-Bouldin", False),
    ]

    for ax, (column, title, higher_is_better) in zip(axes.flatten(), metric_specs):
        ax.plot(validity_table["k"], validity_table[column], marker="o", color="#1f77b4", linewidth=2)
        optimal_row = validity_table.loc[validity_table["k"] == optimal_k].iloc[0]
        ax.scatter([optimal_k], [optimal_row[column]], color="#d62728", s=60, zorder=3)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel("k")
        ax.set_ylabel(column)
        ax.grid(True, linestyle=":", alpha=0.4)
        caption = "Higher is better" if higher_is_better else "Lower is better"
        ax.text(0.98, 0.02, caption, transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color="#666666")

    plt.tight_layout()
    plt.savefig(output_path, dpi=DPI_SETTING, bbox_inches="tight", format="png")
    plt.close(fig)


def save_cluster_scatter_grid(assignments: pd.DataFrame, output_path: str | Path) -> None:
    """Plot pairwise composite scores colored by cluster."""
    output_path = ensure_parent_dir(output_path)
    pairs = [
        ("Economic Score", "Environmental Score"),
        ("Economic Score", "Social Score"),
        ("Environmental Score", "Social Score"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    plt.subplots_adjust(top=0.95, bottom=0.08, left=0.07, right=0.98, wspace=0.30, hspace=0.30)
    flat_axes = axes.flatten()
    cluster_counts = assignments["Cluster"].value_counts().sort_index().to_dict()
    clusters = sorted(assignments["Cluster"].unique())

    for axis, (x_column, y_column) in zip(flat_axes[:3], pairs):
        colors = [CLUSTER_COLORS[(int(cluster_id) - 1) % len(CLUSTER_COLORS)] for cluster_id in assignments["Cluster"]]
        axis.scatter(
            assignments[x_column],
            assignments[y_column],
            s=56,
            c=colors,
            alpha=0.9,
            edgecolors="white",
            linewidth=0.7,
            zorder=3,
        )
        add_offset_labels(axis, assignments[x_column], assignments[y_column], assignments["Code"], colors, font_size=8.2)
        axis.set_xlabel(x_column.replace(" Score", ""), fontweight="bold", fontsize=12)
        axis.set_ylabel(y_column.replace(" Score", ""), fontweight="bold", fontsize=12)
        axis.set_xlim(-0.05, 1.05)
        axis.set_ylim(-0.05, 1.05)
        axis.grid(True, linestyle=":", alpha=0.5)
        axis.tick_params(labelsize=11)

    flat_axes[3].axis("off")
    legend_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=CLUSTER_COLORS[(cluster - 1) % len(CLUSTER_COLORS)],
            markersize=12,
            label=f"Cluster {cluster} (n={cluster_counts.get(cluster, 0)})",
        )
        for cluster in clusters
    ]
    flat_axes[3].legend(handles=legend_handles, loc="center", title="Cluster groups", title_fontsize=13, fontsize=12, frameon=False)
    flat_axes[3].text(0.5, 0.18, "(Letters = country codes with leader lines)", ha="center", color="#555555", fontsize=11, transform=flat_axes[3].transAxes)
    plt.savefig(output_path, dpi=DPI_SETTING, bbox_inches="tight", format="jpg")
    plt.close(fig)


def save_cluster_radar_chart(assignments: pd.DataFrame, output_path: str | Path) -> None:
    """Plot the average dimension profile for each cluster."""
    output_path = ensure_parent_dir(output_path)
    profiles = assignments.groupby("Cluster")[[f"{dimension} Score" for dimension in DIMENSIONS]].mean()
    labels = DIMENSIONS
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, axis = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    for cluster in sorted(profiles.index):
        values = profiles.loc[cluster].tolist()
        values += values[:1]
        color = CLUSTER_COLORS[(cluster - 1) % len(CLUSTER_COLORS)]
        axis.plot(angles, values, linewidth=2, linestyle="solid", label=f"Cluster {cluster}", color=color)
        axis.fill(angles, values, color=color, alpha=0.15)

    axis.set_theta_offset(np.pi / 2)
    axis.set_theta_direction(-1)
    axis.set_xticks(angles[:-1])
    axis.set_xticklabels(labels, fontweight="bold", fontsize=11)
    axis.set_ylim(0, 0.8)
    axis.set_yticks([0.2, 0.4, 0.6])
    axis.set_yticklabels(["0.2", "0.4", "0.6"], color="grey", size=8)
    plt.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), frameon=False)
    plt.savefig(output_path, dpi=DPI_SETTING, bbox_inches="tight", format="jpg")
    plt.close(fig)
