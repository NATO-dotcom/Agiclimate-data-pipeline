# dbt Project — `agri_climate_models`

This dbt project implements the **Silver → Gold** transformations for the Agri-Climate Data Pipeline using **DuckDB** as the warehouse engine with **MinIO S3** integration.

## Quick Start

```bash
cd warehouse/agri_climate_models
export DBT_PROFILES_DIR=$(pwd)
dbt build
```

## Model Dependency Graph

```
sources (MinIO Parquet)
  ├── stg_crops (view)      ── denormalized yields + fields + regions
  ├── stg_weather (view)    ── aggregated annual weather per region
  └── crop_categories (seed) ── static crop → category mapping
          │
          ▼
  climate_impact_analysis (table) ── final analytics join
```

## Project Structure

| Directory     | Contents |
| ------------- | -------- |
| `models/staging/` | `stg_crops.sql`, `stg_weather.sql`, `sources.yml`, `schema.yml` |
| `models/marts/`   | `climate_impact_analysis.sql` |
| `seeds/`          | `crop_categories.csv` |
| `macros/`         | `convert_kg_to_tons.sql` |
| `tests/`          | `assert_positive_metrics.sql` |
| `snapshots/`      | `fields_snapshot.sql` (SCD Type 2 on `soil_type`) |

## Profile

Defined in `profiles.yml` — connects DuckDB to MinIO via `httpfs` + `aws` extensions. Uses `127.0.0.1:9000` as the S3 endpoint (local MinIO).

> **Note**: For full documentation on this dbt project's models, tests, and integration with the pipeline, see the main [README.md](../../README.md) in the project root.
