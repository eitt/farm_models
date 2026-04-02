# Methodology

Docx target: this file is written to replace and strengthen the current methodology section in `Methodology and Results.docx`.

## Empirical Design

The implemented pipeline proceeds in four stages:

1. Load the three worksheet pillars from `data.xlsx`: Economic, Environmental, and Social.
2. Reorient indicators so that higher values always represent better sustainability performance.
3. Estimate entropy weights and build composite scores for each pillar.
4. Benchmark countries with mean-plus/minus-standard-deviation classes and identify cross-country regimes through Ward hierarchical clustering.

## Data Structure

Each worksheet contains one `COUNTRY` column followed by the indicator columns for a single sustainability pillar. The analysis treats countries as alternatives and indicators as decision criteria.

## Orientation

Let `x_ij` denote the raw value for country `i` on indicator `j`. The oriented value `x*_ij` is defined as:

- `x*_ij = x_ij` for benefit indicators
- `x*_ij = -x_ij` for cost indicators

This transformation ensures directional consistency before normalization and aggregation.

## Entropy Probabilities

For each indicator `j`, the oriented values are converted into column-wise probability shares:

`p_ij = x*_ij / sum_i x*_ij`

When a column sum is zero, the implementation assigns zero probabilities for that column to avoid division errors. These probabilities are used only for the entropy calculation, not for the final score itself.

## Shannon Entropy And Diversity

For each indicator:

- `e_j = -k * sum_i p_ij * ln(p_ij)`
- `k = 1 / ln(n)`
- `d_j = 1 - e_j`

Here, `n` is the number of countries, `e_j` is entropy, and `d_j` is the degree of diversification. Indicators with greater dispersion produce larger diversity scores.

## Indicator Weights

The final entropy weight for indicator `j` is:

`w_j = d_j / sum_j d_j`

The weights are normalized within each pillar, so the pillar weights sum to `1`.

## Composite Scores

The oriented indicator matrix is min-max normalized column by column:

`z_ij = (x*_ij - min_i x*_ij) / (max_i x*_ij - min_i x*_ij)`

The pillar score for country `i` is then:

`Score_i = sum_j w_j * z_ij`

This yields one score per country for the Economic, Environmental, and Social dimensions.

## Descriptive Classification

For the EU-27 subset, each dimension score is classified using the sample mean `mu` and standard deviation `sigma`:

- `High`: `x > mu + sigma`
- `Medium-high`: `mu < x <= mu + sigma`
- `Medium-low`: `mu - sigma < x <= mu`
- `Low`: `x <= mu - sigma`

This classification is descriptive and visual. Statistical interpretation should remain anchored in the continuous scores.

## Hierarchical Clustering

The local project replicates the notebook by clustering on weighted normalized indicator features. For each pillar, the min-max normalized indicators are multiplied by their entropy weights, and the three weighted blocks are concatenated into a single feature matrix. Ward linkage is then applied using Euclidean distance.

The number of clusters is selected with the gap-statistic one-standard-error rule. Additional diagnostics are reported for transparency:

- silhouette score
- Calinski-Harabasz index
- Davies-Bouldin index
- within-cluster sum of squares

This makes the clustering stage both reproducible and auditable from the exported tables.
