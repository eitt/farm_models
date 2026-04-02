"""Project configuration constants."""

DIMENSIONS = ["Economic", "Environmental", "Social"]

SCHEMA = {
    "Economic": [
        "Net Farm Income ratio",
        "Efficiency",
        "Labour Productivity",
        "Total subsidies/Farm Family Income",
        "Capital Productivity",
    ],
    "Environmental": [
        "Share of UAA for organic farming",
        "Livestock density (Livestock Units/Ha)",
        "Fertilizer usage (Kg/Ha)",
        "Pesticide usage (Kg/Ha)",
        "Energy Intensity (Fuel consumption in liters/Ha)",
        "Water Intensity (Water consumption in m^3/Ha)",
    ],
    "Social": [
        "Family Farm Income/Reference Income",
        "Family Work Unit/Total labour",
        "Other gainful activities/Total output",
        "Structural change rate",
        "Farm use/Total inputs",
    ],
}

COST_COLUMNS = {
    "Economic": ["Total subsidies/Farm Family Income"],
    "Environmental": [
        "Livestock density (Livestock Units/Ha)",
        "Fertilizer usage (Kg/Ha)",
        "Pesticide usage (Kg/Ha)",
        "Energy Intensity (Fuel consumption in liters/Ha)",
        "Water Intensity (Water consumption in m^3/Ha)",
    ],
    "Social": ["Structural change rate"],
}

EU27 = {
    "(AT) Austria",
    "(BE) Belgium",
    "(BG) Bulgaria",
    "(HR) Croatia",
    "(CY) Cyprus",
    "(CZ) Czechia",
    "(DK) Denmark",
    "(EE) Estonia",
    "(FI) Finland",
    "(FR) France",
    "(DE) Germany",
    "(EL) Greece",
    "(HU) Hungary",
    "(IE) Ireland",
    "(IT) Italy",
    "(LV) Latvia",
    "(LT) Lithuania",
    "(LU) Luxembourg",
    "(MT) Malta",
    "(NL) Netherlands",
    "(PL) Poland",
    "(PT) Portugal",
    "(RO) Romania",
    "(SK) Slovakia",
    "(SI) Slovenia",
    "(ES) Spain",
    "(SE) Sweden",
}

CLASS_ORDER = ["Low", "Medium-low", "Medium-high", "High"]

SD_COLORS = {
    "Low": "#d73027",
    "Medium-low": "#fc8d59",
    "Medium-high": "#91cf60",
    "High": "#1a9850",
}

CLUSTER_COLORS = ["#2ca02c", "#1f77b4", "#ff7f0e", "#d62728", "#9467bd"]

MAP_NAME_FIXES = {
    "Czechia": "Czech Rep.",
    "Bosnia and Herzegovina": "Bosnia and Herz.",
    "North Macedonia": "Macedonia",
}

DEFAULT_INPUT_FILE = "data.xlsx"
DEFAULT_OUTPUT_DIR = "outputs"

A4_WIDTH_INCHES = 8.27
DPI_SETTING = 300

WORKBOOK_SHEET_DESCRIPTIONS = {
    "README": "This workbook consolidates the entropy pipeline inputs, transformations, scores, and clustering diagnostics.",
    "Data": "Raw numeric indicators merged across the Economic, Environmental, and Social sheets.",
    "Oriented": "Indicator matrix after cost indicators are multiplied by -1 so higher values always mean better sustainability performance.",
    "Probabilities": "Column-wise probability shares derived from the oriented matrix and used only for Shannon entropy weighting.",
    "Norm01": "Min-max normalized indicators on the [0, 1] interval after orientation.",
    "Entropy_Weights": "Entropy-based indicator weights within each sustainability dimension.",
    "Scores_Wide": "Per-country composite scores for the Economic, Environmental, and Social dimensions.",
    "Sankey_Links": "Indicator-to-dimension links for Sankey plotting, with link magnitude equal to the entropy weight.",
    "EU_SD_Classes": "EU-only scores annotated with mean-plus/minus-standard-deviation performance classes.",
    "EU_SD_Stats": "EU-only descriptive statistics used to define the four benchmark classes.",
    "Cluster_Validity": "Ward-clustering diagnostics across tested values of k, including gap statistic, silhouette, Calinski-Harabasz, and Davies-Bouldin.",
    "Cluster_Assignments": "Country-level cluster membership and composite dimension scores.",
}
