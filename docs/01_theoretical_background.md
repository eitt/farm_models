# Theoretical Background

Docx target: use this file to expand the conceptual framing before the current methodology section in `Methodology and Results.docx`.

## Why A Composite Sustainability Framework Is Needed

Agricultural sustainability is inherently multidimensional. Economic viability, environmental pressure, and social resilience rarely move in the same direction or with the same intensity. A single descriptive statistic is therefore insufficient unless it is built from a transparent aggregation rule that preserves the information carried by several indicators at once. In this project, the composite framework serves two purposes:

- to condense several farm-system indicators into interpretable dimension scores
- to preserve cross-country heterogeneity rather than hide it under a simple average

## Why Use Shannon Entropy Weights

The Shannon entropy method provides objective, data-driven weights. The intuition is straightforward: an indicator that barely varies across countries contributes little discriminatory information, while an indicator with strong cross-country variation helps separate sustainability profiles more clearly. Entropy weighting is therefore attractive when the goal is comparative benchmarking and when the study prefers to avoid arbitrary expert scoring.

In this setting, the entropy method rewards dispersion rather than normative importance. That distinction matters. A high weight does not mean that an indicator is philosophically more important than the others; it means that the indicator is empirically more informative for differentiating countries in the observed dataset.

## Why Orientation Is Necessary

Indicators do not all point in the same normative direction. For benefit indicators, higher values represent stronger sustainability performance. For cost indicators, higher values represent pressure or vulnerability. Before any weighting or aggregation can be justified, those directions must be aligned. The project therefore reorients cost indicators by multiplying them by `-1`, so larger values always mean better performance after orientation.

## Why Min-Max Scaling Is Used For Scores

Entropy probabilities are useful for weighting because they capture relative dispersion within each indicator. They are less intuitive as direct score inputs because the resulting values are not naturally bounded in a policy-friendly range. Min-max normalization solves that problem by translating each oriented indicator into the `[0, 1]` interval. The composite dimension score can then be interpreted as a weighted achievement index where `1` is the within-sample best performer and `0` is the within-sample worst performer for a given indicator.

## Why Hierarchical Clustering Complements Composite Scores

Composite scores rank countries within each dimension, but they do not reveal whether countries form broader sustainability regimes. Ward hierarchical clustering adds that second layer of interpretation. By minimizing the increase in within-cluster variance at each merge, Ward linkage identifies compact groups of countries with similar multidimensional profiles. This is especially useful when the research question concerns structural patterns, trade-offs, or regime-type differences rather than only best-versus-worst rankings.

## Interpretation Principle

The framework should be read as a comparative and exploratory tool, not a causal model. The scores identify relative standing within the sample, and the clusters identify similarity structures in the weighted indicator space. They do not, on their own, establish causal relationships between policy, geography, farm structure, and sustainability outcomes. That distinction should be made explicit in the Word report.
