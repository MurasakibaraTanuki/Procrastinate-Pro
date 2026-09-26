# Case brief

Procrastinate Pro+ is a fictional entertainment application that remained unprofitable despite substantial advertising expenditure. The task is to identify the sources of weak marketing efficiency using user activity from 1 May to 27 October 2019.

## Input tables

### `visits_info_short.csv`

| Column | Description |
|---|---|
| `User Id` | Unique user identifier |
| `Region` | User country |
| `Device` | Device category |
| `Channel` | Acquisition source |
| `Session Start` | Session start timestamp |
| `Session End` | Session end timestamp |

### `orders_info_short.csv`

| Column | Description |
|---|---|
| `User Id` | Unique user identifier |
| `Event Dt` | Purchase timestamp |
| `Revenue` | Order revenue |

### `costs_info_short.csv`

| Column | Description |
|---|---|
| `dt` | Campaign date |
| `Channel` | Advertising source |
| `costs` | Daily advertising spend |

## Analytical scope

1. Validate and prepare the source tables.
2. Construct acquisition profiles at user level.
3. Compare user volume and payer share by country, device and channel.
4. Evaluate marketing spend and CAC.
5. Calculate 14-day LTV, ROI, conversion and retention.
6. Identify segments that weaken payback and propose testable actions.

The business target assumes that acquisition expenditure should be recovered within 14 days.
