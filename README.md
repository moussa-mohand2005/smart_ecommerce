# Smart Fashion Intelligence

Smart Fashion Intelligence is an MLOps product intelligence project for e-commerce stores. It automates the collection of products from Shopify/WooCommerce stores, enriches data with LLMs, applies ML analytics to select the best products, then exposes results in an interactive BI dashboard.

The main use case is intelligent analysis of fashion products: clothing (shirts, jackets, dresses, pants, hoodies...) and footwear (sneakers, boots, sandals, heels...) for all demographics (men, women, kids, unisex).

**Live dashboard:** [smart-shoe-dashboard-7qch3vsahq-uc.a.run.app](https://smart-shoe-dashboard-7qch3vsahq-uc.a.run.app)

## Objectives

- Automatically scrape products from Shopify/WooCommerce stores.
- Filter fashion products (clothing & footwear) with keyword rules and LLM validation.
- Enrich product listings with technical attributes: material, fit/sole type, closure, gender, season, style type, short description, and marketing persona.
- Calculate an ML score to identify the most attractive products.
- Export a Top-K selection of the best products.
- Visualize KPIs, trends, clusters, and recommendations in a responsive Next.js application.
- Orchestrate the workflow with an MLOps/Kubeflow pipeline.
- Control data access via a responsible MCP-style server.
- Automate basic tests with GitHub Actions.

## Architecture

```text
E-commerce Sources (45 Shopify/WooCommerce stores)
    |
    v
step1_web_scraper.py
    Scraping, crawling, Shopify/WooCommerce detection, MySQL insertion
    Target: 5000 products (clothing + footwear)
    |
    v
step2_llm_enrichment.py
    Gemini/Groq enrichment, technical attributes, persona
    |
    v
step3_ml_analytics.py
    Scoring, Top-K, clustering, PCA, XGBoost, association rules
    |
    +--> top_k_products.csv
    +--> fashion_correlations.csv
    |
    v
dashboard-next/
    Next.js dashboard, server APIs, AI insights, and MCP tools

Orchestration:
    step5_mlops_pipeline.py
    kubeflow_pipeline.py
    shoe_pipeline.yaml

Responsible AI:
    step6_responsible_ai_mcp.py
```

## Project Structure

| File | Role |
|---|---|
| `step1_web_scraper.py` | Scraping Shopify/WooCommerce, HTML crawling, product extraction, DB insertion |
| `step2_llm_enrichment.py` | LLM enrichment with Gemini/Groq |
| `step3_ml_analytics.py` | ML scoring, clustering, PCA, XGBoost, Top-K |
| `dashboard-next/` | Production Next.js dashboard and server-side APIs |
| `step4_bi_dashboard.py` | Legacy Streamlit dashboard |
| `step5_mlops_pipeline.py` | Local pipeline that runs steps 1, 2, and 3 |
| `step6_responsible_ai_mcp.py` | MCP-style read-only server with validation and audit log |
| `kubeflow_pipeline.py` | Kubeflow pipeline definition with `kfp` SDK |
| `shoe_pipeline.yaml` | Compiled Kubeflow pipeline |
| `schema.sql` | MySQL schema for `shops` and `products` tables |
| `fashion_stores_shopify_woocommerce.xlsx` | Input store list (45 stores) |
| `Dockerfile` | Docker image for the pipeline |
| `docker-compose.yml` | Base for launching services with Docker Compose |
| `.github/workflows/ci.yml` | Python and Next.js CI checks |
| `.env.example` | Configuration example without real secrets |

## Step 1: Data Scraping

Scraping is implemented in `step1_web_scraper.py`.

Features:

- Reads an Excel file containing stores to analyze.
- Automatic platform detection: Shopify, WooCommerce, or other.
- Extraction via Shopify `/products.json`.
- Extraction via Shopify sitemap.
- HTML fallback crawling for product pages.
- Parsing with `requests` and `BeautifulSoup`.
- Fashion filtering by keywords (clothing + footwear).
- Optional LLM validation to avoid false positives.
- Automatic category, subcategory, and gender classification.
- Insertion of products into MySQL.
- Target: **5000 products** from **45 stores**.

Data extracted:

- Product title
- Current price (USD)
- Availability
- Description
- Vendor / store
- Category (Clothing / Footwear)
- Subcategory (T-Shirts, Sneakers, Dresses, Boots, etc.)
- Brand
- Main image
- Product URL

## Step 2: LLM Enrichment

Enrichment is implemented in `step2_llm_enrichment.py`.

Supported providers:

- Google Gemini
- Groq

Generated attributes:

- `material`
- `sole_type` (footwear) / fit type (clothing)
- `closure`
- `gender`
- `season`
- `style_type`
- `short_description`
- `persona_json`

API keys are configured via `.env`.

## Step 3: ML Analytics & Top-K

Analysis is implemented in `step3_ml_analytics.py`.

The ML score combines several metrics:

- Average rating
- Number of reviews
- Normalized price
- Stock availability

The script also applies:

- `KMeans` for style clustering (up to 8 clusters)
- `PCA` for 2D visualization
- `XGBoost` to predict potential success
- `mlxtend` for association rules
- Export Top-K to `top_k_products.csv`
- Export correlations to `fashion_correlations.csv`

## Step 4: BI Dashboard

The production dashboard is implemented with Next.js in `dashboard-next/`. It reads MySQL only through server-side route handlers, keeps credentials out of the browser, and uses server-side filtering and pagination. The previous Streamlit implementation remains in `step4_bi_dashboard.py` as a legacy reference.

Features:

- Global KPIs
- Curated Top Picks
- Market Trends
- Style Clusters
- Brand Intelligence
- Data Explorer
- AI Insight Hub
- Responsible AI View

Launch the dashboard locally:

```powershell
cd dashboard-next
npm ci
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Step 5: Kubeflow Pipelines

The Kubeflow pipeline is defined in `kubeflow_pipeline.py`.

Compile the pipeline:

```powershell
python kubeflow_pipeline.py
```

## Step 6: Responsible AI with MCP-style Server

The file `step6_responsible_ai_mcp.py` exposes a simplified MCP-style server.

Applied principles:

- Read-only data access
- Whitelist of authorized tools
- Parameter validation
- Maximum result limit
- Logging to `mcp_audit.log`
- No direct secret exposure

Exposed tools:

- `get_top_products`
- `analyze_cluster`
- `get_shop_ranking`
- `get_category_stats`

## Prerequisites

- Python 3.10 or 3.11
- Node.js 24 or newer
- MySQL 8.0 or compatible MariaDB
- Docker optional
- Kubernetes required only for real Kubeflow execution

## Local Installation

Create a Python environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create the MySQL database:

```sql
CREATE DATABASE smart_ecommerce;
```

Import the schema:

```powershell
mysql -u root -p smart_ecommerce < schema.sql
```

Configure `.env`:

```env
DB_HOST=localhost
DB_USER=root
DB_PASS=your_mysql_password
DB_NAME=smart_ecommerce
SHOP_INPUT_FILE=fashion_stores_shopify_woocommerce.xlsx

GEMINI_KEYS=your_gemini_key
GROQ_KEYS=your_groq_key
```

## Local Execution

Run the full local pipeline:

```powershell
python step5_mlops_pipeline.py
```

Or run steps separately:

```powershell
python step1_web_scraper.py
python step2_llm_enrichment.py
python step3_ml_analytics.py
```

Launch the production dashboard locally:

```powershell
cd dashboard-next
npm ci
npm run dev
```

## Generated Artifacts

| Artifact | Description |
|---|---|
| `shoe_pipeline.yaml` | Compiled Kubeflow pipeline |
| `top_k_products.csv` | Selection of the best products |
| `fashion_correlations.csv` | Association rules between fashion attributes |
| `mcp_audit.log` | MCP-style tool access logs |

## Dashboard API

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/dashboard` | Filtered KPIs, charts, products, and pagination |
| `POST` | `/api/insights` | AI-generated strategic market brief |
| `GET` | `/api/mcp` | Lists controlled database tools |
| `POST` | `/api/mcp` | Executes a validated MCP-style tool |

## Quality Checks

```powershell
python -c "from pathlib import Path; [compile(p.read_text(encoding='utf-8'), str(p), 'exec') for p in Path('.').glob('*.py')]"
cd dashboard-next
npm run typecheck
npm run build
```

GitHub Actions runs equivalent Python and Next.js checks for every push and pull request targeting `main`.

## Docker

Run the dashboard without starting the paid scraping pipeline:

```powershell
docker compose up --build dashboard
```

The Python pipeline is behind an explicit Compose profile:

```powershell
docker compose --profile pipeline run --rm app
```

## Google Cloud Deployment

The live deployment is hosted in project `tangier-weather-de-2026-0718`:

- Cloud Run service: `smart-shoe-dashboard`
- Cloud SQL instance: `smart-shoe-mysql` in `us-central1`
- Secret Manager for database and provider credentials
- Vertex AI fallback for AI Insight reports
- Dedicated least-privilege runtime service account

Cloud Run connects through the Cloud SQL connector. The database has deletion protection enabled and no externally authorized network ranges.

## Security

- Never commit `.env` or provider credentials; `.env.example` contains placeholders only.
- SQL filters and MCP tools use parameterized queries.
- Database and AI credentials remain server-side.
- External catalog values are rendered as React text instead of injected HTML.
- Secret Manager versions are pinned in the deployed Cloud Run revision.

## Known Limitations

- Scraped classifications still require stronger validation and may contain non-fashion products.
- The predictive target is derived from internal catalog signals and is not a substitute for real sales labels.
- Kubeflow components are demonstrative until the production scripts and dependencies are packaged into their component images.
- Unit and integration test coverage should be expanded beyond the current build and syntax checks.

