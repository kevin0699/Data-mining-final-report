# EV Adoption, Charging Buildout, and Consumer Interest Across Four Markets

This repository archives the final project materials for a data visualization study of EV demand, charging infrastructure, and consumer interest across four countries.

## Repository Contents

- `build_final_project_assets.py`: Python script that reads the merged market dataset and generates the visualization assets.
- `final_project_main_figure.svg`: Main figure used in the report.
- `final_project_report_draft.html`: Three-page report prepared for final submission.
- `final_project_summary.json`: Computed summary statistics used to support findings.
- Original dataset files from the Kaggle package, including `ev_market_master.csv` and the local `README.md`.

## Project Question

How do EV sales, charging infrastructure, and consumer interest evolve together across national markets?

## Main Findings

- India shows the fastest relative EV expansion in the dataset: monthly sales rise from 316 in 2019-01 to 7,536 in 2023-12, a 23.85x increase.
- France and the United Kingdom finish 2023 at the largest monthly sales volumes (39,704 and 40,000), and both markets show very strong sales–charger co-movement (r = 0.968 and 0.962).
- The Netherlands has the largest charger base by 2023-12 (163,800), but its sales peak earlier (2021-01-01) and remain much flatter than France or the UK.
- Search interest is not a universal proxy for demand: the UK reaches 40,000 monthly sales in 2023-12 while "electric vehicle" search interest falls to 37.7.

## Data Sources

The local dataset README cites the following sources:

- IEA Global EV Outlook 2024 (https://www.iea.org/reports/global-ev-outlook-2024)
- Google Trends via pytrends
- BYD Co. Ltd monthly sales press releases
- Tesla IR quarterly reports
- AFDC (US DOE Alternative Fuels Station Locator)
- IEA Charging Infrastructure data
- GlobalPetrolPrices.com / IEA Energy Prices
