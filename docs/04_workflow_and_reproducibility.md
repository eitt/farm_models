# Workflow And Reproducibility

Docx target: use this file to add a stronger reproducibility note or appendix to `Methodology and Results.docx`.

## What Changed Relative To The Notebook

The original Colab notebook is still present in the repository, but its logic is now mirrored by a local project with explicit functional modules. The refactor removes Colab-only assumptions such as:

- hard-coded `/content/` paths
- notebook-cell execution order dependencies
- `pip install` cells mixed with analysis code

## Project Flow

The new local flow is:

1. `main.py` launches the pipeline.
2. `farm_models/analysis.py` loads the workbook and assembles export tables.
3. `farm_models/entropy.py` handles orientation, entropy probabilities, weights, and scores.
4. `farm_models/clustering.py` builds the weighted feature matrix and runs Ward clustering.
5. `farm_models/plots.py` exports the Sankey, score, scatter, dendrogram, validity, and radar figures.
6. `farm_models/mapping.py` optionally creates geographic maps when `geopandas` is available.

## Command

Core run:

```bash
python main.py --skip-maps
```

Full run with maps:

```bash
pip install geopandas
python main.py
```

## Output Structure

The pipeline writes:

- `outputs/tables/Entropy_Pipeline_Outputs.xlsx`
- `outputs/tables/Cluster_Assignments.csv`
- `outputs/tables/Clustering_Features_Weighted.csv`
- `outputs/tables/Cluster_Validity_Metrics.csv`
- `outputs/figures/`
- `outputs/run_summary.json`

## Why This Improves The Project

The refactor makes the analytical logic easier to audit because inputs, transformations, and outputs are no longer mixed in large notebook cells. It also makes it easier to revise the report, since each methodological statement can now be traced to a dedicated function or exported table.
