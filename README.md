# Farm Models

This repository studies the sustainability profiles of EU-27 agriculture using Shannon entropy weighting, min-max composite scoring, and Ward hierarchical clustering. The original Colab notebook is preserved in the repository, and the same workflow is now replicated as a function-based Python project that runs locally from a single entrypoint.

## Authors

### Stamatis Mantziaris

Stamatis Mantziaris graduated from the Faculty of Agricultural Economics and Rural Development at the Agricultural University of Athens and holds an MBA in Food & Agribusiness from the same university. He is a PhD candidate in Agricultural Economics and Policy at the Agricultural University of Athens. He has participated in EU and national research projects related to policy analysis in agriculture and the bioenergy sector. In the context of his collaboration with the Agricultural Economics Research Institute, he worked as a research assistant for the National Fisheries Data Collection Program 2017-2019. His research interests focus on policy analysis in the primary sector, supply-response modeling of arable farming, economic evaluation of energy crops, and agribusiness investment appraisal.

E-mail: `sta.athens@hotmail.com`  
Occupation: `Research Associate`  
Full CV reference provided by the author: `CV_MANTZIARIS_5_2018_EN.pdf`

### Leonardo Talero-Sarmiento

Leonardo Talero-Sarmiento is a Ph.D. in Engineering from the Universidad Autonoma de Bucaramanga, with expertise in mathematical modeling, data analytics, operations research, manufacturing systems, process improvement, and technology adoption. His research addresses decision-making and production-planning challenges in agricultural and industrial contexts, applying operations research, bibliometric analysis, systematic reviews, and machine-learning methods to strengthen value-chain resilience, optimize healthcare delivery, and drive digital transformation. He regularly publishes in peer-reviewed journals including *Heliyon*, *Cogent Engineering*, *Ecological Informatics*, *AgriEngineering*, *Big Data and Cognitive Computing*, *Digital Policy, Regulation and Governance*, *Revista Colombiana de Computacion*, *Suma de Negocios*, *IngeCUC*, *Apuntes del Cenes*, *Estudios Gerenciales*, and *Contaduria y Administracion*.

## Repository Layout

```text
.
|-- [2025_2]_Farm_Models_EU.ipynb
|-- data.xlsx
|-- Methodology and Results.docx
|-- main.py
|-- requirements.txt
|-- farm_models/
|   |-- analysis.py
|   |-- clustering.py
|   |-- config.py
|   |-- entropy.py
|   |-- mapping.py
|   |-- pipeline.py
|   `-- plots.py
`-- docs/
```

## Running The Project

The default command now bootstraps the environment and then runs the full pipeline, including the geographic map output when the Natural Earth geometry can be downloaded:

```bash
python main.py
```

If you want the script to also force package upgrades:

```bash
python main.py --upgrade-deps
```

If your environment is already prepared and you want to skip the bootstrap step:

```bash
python main.py --no-bootstrap
```

## Outputs

The pipeline writes reproducible outputs into `outputs/`:

- `outputs/tables/Entropy_Pipeline_Outputs.xlsx`
- `outputs/tables/Cluster_Assignments.csv`
- `outputs/tables/Clustering_Features_Weighted.csv`
- `outputs/tables/Cluster_Validity_Metrics.csv`
- `outputs/figures/*.jpg`
- `outputs/run_summary.json`

## Documentation

The `docs/` folder contains Markdown files designed to strengthen the current `Methodology and Results.docx` without deleting or replacing it. They separate the project into theoretical background, methodology, data design, workflow, results interpretation, and revision guidance for the Word document.

## Notes

- The original Colab notebook is intentionally preserved: `[2025_2]_Farm_Models_EU.ipynb`
- The refactor avoids object-oriented design and uses plain functions to keep inputs, calculations, and flows explicit.
- `main.py` now installs or refreshes the packages in `requirements.txt` before launching the pipeline unless `--no-bootstrap` is used.
- Map generation is included in the default pipeline run and depends on `geopandas` plus access to Natural Earth geometries.
