# Data And Indicator Design

Docx target: use this file to make the data and indicator-description parts of `Methodology and Results.docx` more explicit and reproducible.

## Workbook Logic

The project reads a single Excel workbook, `data.xlsx`, with three sheets:

- `Economic`
- `Environmental`
- `Social`

Each sheet contains the same observational unit, `COUNTRY`, and a different set of indicators for the corresponding sustainability pillar.

## Economic Pillar

Indicators:

- Net Farm Income ratio
- Efficiency
- Labour Productivity
- Total subsidies/Farm Family Income
- Capital Productivity

Orientation rule:

- `Total subsidies/Farm Family Income` is treated as a cost indicator because stronger dependence on subsidies is interpreted as lower autonomous economic sustainability.
- The remaining indicators are treated as benefit indicators.

## Environmental Pillar

Indicators:

- Share of UAA for organic farming
- Livestock density (Livestock Units/Ha)
- Fertilizer usage (Kg/Ha)
- Pesticide usage (Kg/Ha)
- Energy Intensity (Fuel consumption in liters/Ha)
- Water Intensity (Water consumption in m^3/Ha)

Orientation rule:

- Organic share is treated as a benefit indicator.
- Livestock density, fertilizer usage, pesticide usage, energy intensity, and water intensity are treated as cost indicators because larger values imply stronger environmental pressure.

## Social Pillar

Indicators:

- Family Farm Income/Reference Income
- Family Work Unit/Total labour
- Other gainful activities/Total output
- Structural change rate
- Farm use/Total inputs

Orientation rule:

- Structural change rate is treated as a cost indicator in the implemented notebook replication.
- The remaining indicators are treated as benefit indicators.

## Practical Interpretation

The indicator design matters because entropy weights are sensitive to dispersion. If a conceptually important variable changes little across countries, it will receive a lower empirical weight than a more unevenly distributed variable. This should be framed clearly in the report to avoid confusing empirical importance with normative importance.

## Suggested Wording For The Word Report

The report should make three points explicit:

1. The workbook is pillar-structured rather than flat, which keeps the economic, environmental, and social concepts analytically distinct.
2. Indicator direction is standardized before any aggregation is attempted.
3. The final scores are pillar-specific composites, not a single global sustainability index.
