# Revision Guide For `Methodology and Results.docx`

This guide explains how the Markdown files in `docs/` should improve the current Word report while keeping the `.docx` file in the repository.

## Main Issues In The Current Word Draft

### 1. Theoretical framing is too compressed

The current draft moves quickly into formulas and results. It should spend more time explaining why entropy weighting and hierarchical clustering are suitable for this research problem.

Use:

- `docs/01_theoretical_background.md`

### 2. The methodology needs tighter alignment with the implemented code

The report should describe the actual local pipeline clearly:

- workbook with three sheets
- cost/benefit orientation
- entropy probabilities
- entropy weights
- min-max score construction
- Ward clustering on weighted normalized features
- gap-statistic one-standard-error rule

Use:

- `docs/02_methodology.md`
- `docs/04_workflow_and_reproducibility.md`

### 3. Indicator design should be explicit

Readers should not have to infer which variables are treated as cost indicators. The report should name the indicators and explain their orientation.

Use:

- `docs/03_data_and_indicator_design.md`

### 4. Results should rely on verified values

The current local run confirms the main interpretations already present in the draft, but the narrative should be updated using the exact verified outputs exported by the pipeline.

Use:

- `docs/05_results_and_interpretation.md`

### 5. The report should distinguish descriptive benchmarking from inference

The mean-plus/minus-standard-deviation classes are useful for communication, but they are descriptive labels, not inferential evidence. That limitation should be stated directly.

## Recommended Integration Order

1. Add the conceptual framing from `01_theoretical_background.md`.
2. Replace the current methods section with `02_methodology.md`.
3. Insert the indicator explanation from `03_data_and_indicator_design.md`.
4. Add a short reproducibility note from `04_workflow_and_reproducibility.md`.
5. Rewrite the results section using `05_results_and_interpretation.md`.

## Preservation Note

The Word document is intentionally not deleted. The Markdown files are a structured improvement layer for the same study, not a replacement of the original artifact.
