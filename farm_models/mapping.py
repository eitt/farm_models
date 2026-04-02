"""Optional geographic mapping helpers."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import requests

from farm_models.config import MAP_NAME_FIXES, SD_COLORS


def import_geopandas():
    """Import geopandas lazily so the rest of the pipeline can run without it."""
    try:
        import geopandas as gpd
    except ImportError as exc:
        raise RuntimeError(
            "Map generation requires the optional dependency 'geopandas'. Install it to produce the EU choropleth figure."
        ) from exc
    return gpd


def load_world_geometries(cache_dir: str | Path):
    """Load Natural Earth boundaries from cache, download, or a geopandas fallback."""
    gpd = import_geopandas()
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    extract_dir = cache_dir / "naturalearth_50m"
    shapefiles = list(extract_dir.rglob("*.shp"))
    if shapefiles:
        return gpd.read_file(shapefiles[0])

    url = "https://naturalearth.s3.amazonaws.com/50m_cultural/ne_50m_admin_0_countries.zip"
    try:
        response = requests.get(url, headers={"User-Agent": "farm-models-pipeline/1.0"}, timeout=60)
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            archive.extractall(extract_dir)
        shapefiles = list(extract_dir.rglob("*.shp"))
        if shapefiles:
            return gpd.read_file(shapefiles[0])
    except Exception:
        pass

    try:
        dataset_path = gpd.datasets.get_path("naturalearth_lowres")
        return gpd.read_file(dataset_path)
    except Exception as exc:
        raise RuntimeError(
            "Geographic plotting could not obtain Natural Earth geometries. Re-run with network access or place the shapefile in outputs/cache/naturalearth_50m."
        ) from exc


def save_eu_maps(eu_scores, output_path: str | Path, cache_dir: str | Path) -> None:
    """Plot the EU dimension classes on a Europe map."""
    world = load_world_geometries(cache_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    map_data = eu_scores.copy()
    map_data["clean_name"] = map_data["COUNTRY"].str.replace(r"^\(..\)\s+", "", regex=True)
    map_data["clean_name"] = map_data["clean_name"].replace(MAP_NAME_FIXES)

    merge_left = "NAME" if "NAME" in world.columns else "name"
    continent_col = "CONTINENT" if "CONTINENT" in world.columns else "continent"
    merged = world.merge(map_data, left_on=merge_left, right_on="clean_name", how="inner")
    if merged.empty:
        raise RuntimeError("Map generation failed because no country names matched the geometry dataset.")

    context = world[(world[continent_col] == "Europe") | (world[merge_left].isin(["Cyprus", "Turkey"]))].copy()
    context = context[~context[merge_left].isin(merged[merge_left])]
    merged = merged.to_crs(epsg=3035)
    context = context.to_crs(epsg=3035)

    fig, axes = plt.subplots(1, 3, figsize=(20, 10))
    plt.subplots_adjust(wspace=0.05, top=0.90, bottom=0.10)
    class_columns = ["Economic Class", "Environmental Class", "Social Class"]
    titles = ["Economic Dimension", "Environmental Dimension", "Social Dimension"]

    for axis, class_column, title in zip(axes, class_columns, titles):
        context.plot(ax=axis, color="#eeeeee", edgecolor="#bbbbbb", linewidth=0.4)
        merged["current_color"] = merged[class_column].map(SD_COLORS)
        merged.plot(ax=axis, color=merged["current_color"], edgecolor="white", linewidth=0.6)
        axis.set_title(title, fontsize=14, fontweight="bold", pad=15)
        axis.axis("off")
        axis.set_xlim(2500000, 6000000)
        axis.set_ylim(1400000, 5400000)

    legend_elements = [
        mpatches.Patch(facecolor=SD_COLORS[label], edgecolor="white", label=label)
        for label in reversed(list(SD_COLORS.keys()))
    ]
    fig.legend(
        handles=legend_elements,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.15),
        ncol=4,
        fontsize=12,
        frameon=False,
        title="Performance tiers (mu +/- sigma)",
    )
    plt.savefig(output_path, dpi=300, bbox_inches="tight", format="jpg")
    plt.close(fig)
