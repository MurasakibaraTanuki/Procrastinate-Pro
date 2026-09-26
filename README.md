# Procrastinate Pro+ Marketing Analytics

Portfolio project analysing the unit economics of a fictional entertainment app. The analysis examines acquisition cost, lifetime value, return on marketing investment, conversion and retention across channels, regions and devices.

## Business question

Why did large advertising investments fail to produce profitability between May and October 2019, and which acquisition segments should the marketing team prioritise?

## Main findings

- High acquisition costs in the United States and on iPhone traffic offset comparatively strong customer value.
- LambdaMediaAds delivered high LTV but did not recover its acquisition cost within the 14-day target.
- UK and German users showed stronger unit economics than US users.
- Retention declined sharply after the first few days, which limited lifetime value.

These are case-study findings based on the supplied fictional dataset. See the [full report](reports/marketing_analysis.md) for interpretation and recommendations.

## Repository structure

```text
.
├── data/                  # place the three source CSV files here
├── docs/                  # original case brief
├── reports/               # business report
├── src/
│   └── procrastinate_pro/
│       ├── analytics.py   # reusable metric calculations
│       └── cli.py         # command-line entry point
├── tests/                 # unit tests with synthetic data
├── pyproject.toml
└── requirements.txt
```

## Data

The source data are not included in this repository. Add these files to `data/`:

- `visits_info_short.csv`
- `orders_info_short.csv`
- `costs_info_short.csv`

Expected columns are documented in [the case brief](docs/case_brief.md). The `data/` directory is ignored by Git to prevent accidental publication of datasets.

## Installation and use

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python -m procrastinate_pro.cli --data-dir data --output-dir outputs
```

The command validates and cleans the input files, builds user profiles, and exports summary tables as CSV files.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

## Methods

- Cohort horizon: 14 days
- CAC: advertising spend divided by newly acquired users
- LTV: cumulative revenue per acquired user
- ROI: cumulative LTV divided by CAC
- Conversion: cumulative share of users completing a first purchase
- Retention: share of users returning on each lifetime day

## Limitations

The analysis is descriptive and uses a fictional historical dataset. Segment differences do not establish causal effects. The recommendations should be treated as hypotheses for controlled budget experiments rather than guaranteed outcomes.

## Author

Anton Berezin
