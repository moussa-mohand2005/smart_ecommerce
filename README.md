# Smart E-commerce Intelligence

Smart E-commerce Intelligence est un projet MLOps de veille produit pour les boutiques e-commerce. Il automatise la collecte de produits depuis Shopify/WooCommerce, enrichit les donnees avec des LLMs, applique des analyses ML pour selectionner les meilleurs produits, puis expose les resultats dans un dashboard BI interactif.

Le cas d'usage principal est l'analyse intelligente de produits footwear: sneakers, boots, sandals, loafers, heels, etc.

## Objectifs

- Scraper automatiquement des produits depuis des boutiques Shopify/WooCommerce.
- Filtrer les produits footwear avec des regles textuelles et une validation LLM.
- Enrichir les fiches produits avec des attributs techniques: material, sole type, closure, gender, description courte et persona marketing.
- Calculer un score ML pour identifier les produits les plus attractifs.
- Exporter une selection Top-K des meilleurs produits.
- Visualiser les KPIs, tendances, clusters et recommandations dans Streamlit.
- Orchestrer le workflow avec un pipeline MLOps/Kubeflow.
- Encadrer l'acces aux donnees via un serveur MCP-style responsable.
- Automatiser les tests de base avec GitHub Actions.

## Architecture

```text
Sources e-commerce
    |
    v
step1_web_scraper.py
    Scraping, crawling, detection Shopify/WooCommerce, insertion MySQL
    |
    v
step2_llm_enrichment.py
    Enrichissement Gemini/Groq, attributs techniques, persona
    |
    v
step3_ml_analytics.py
    Scoring, Top-K, clustering, PCA, XGBoost, regles d'association
    |
    +--> top_k_products.csv
    +--> footwear_correlations.csv
    |
    v
step4_bi_dashboard.py
    Dashboard BI Streamlit + Plotly

Orchestration:
    step5_mlops_pipeline.py
    kubeflow_pipeline.py
    shoe_pipeline.yaml

Responsible AI:
    step6_responsible_ai_mcp.py
```

## Structure du projet

| Fichier | Role |
|---|---|
| `step1_web_scraper.py` | Scraping Shopify/WooCommerce, crawling HTML, extraction produits, insertion DB |
| `step2_llm_enrichment.py` | Enrichissement LLM avec Gemini/Groq |
| `step3_ml_analytics.py` | Scoring ML, clustering, PCA, XGBoost, Top-K |
| `step4_bi_dashboard.py` | Dashboard Business Intelligence Streamlit |
| `step5_mlops_pipeline.py` | Pipeline local qui lance les etapes 1, 2 et 3 |
| `step6_responsible_ai_mcp.py` | Serveur MCP-style read-only avec validation et audit log |
| `kubeflow_pipeline.py` | Definition du pipeline Kubeflow avec le SDK `kfp` |
| `shoe_pipeline.yaml` | Pipeline Kubeflow compile |
| `schema.sql` | Schema MySQL des tables `shops` et `products` |
| `ci_seed.sql` | Donnees de test pour GitHub Actions |
| `Dockerfile` | Image Docker du pipeline |
| `docker-compose.yml` | Base pour lancer les services avec Docker Compose |
| `.github/workflows/mlops.yml` | Workflow CI/CD |
| `.env.example` | Exemple de configuration sans secrets reels |

## Etape 1: Scraping de donnees

Le scraping est implemente dans `step1_web_scraper.py`.

Fonctionnalites:

- Lecture d'un fichier Excel contenant les boutiques a analyser.
- Detection automatique de plateforme: Shopify, WooCommerce ou autre.
- Extraction via Shopify `/products.json`.
- Extraction via sitemap Shopify.
- Crawling HTML fallback pour les pages produits.
- Parsing avec `requests` et `BeautifulSoup`.
- Filtrage footwear par mots-cles.
- Validation optionnelle avec LLM pour eviter les faux positifs.
- Insertion des produits dans MySQL.

Donnees extraites:

- Titre du produit
- Prix courant
- Disponibilite
- Description
- Vendeur / boutique
- Categorie et sous-categorie
- Marque
- Image principale
- URL produit

## Etape 2: Analyse et Top-K produits

L'analyse est implementee dans `step3_ml_analytics.py`.

Le score ML combine plusieurs metriques:

- Note moyenne
- Nombre d'avis
- Prix normalise
- Disponibilite stock

Le script applique aussi:

- `KMeans` pour le clustering des styles
- `PCA` pour la visualisation 2D
- `XGBoost` pour predire le succes potentiel
- `mlxtend` pour les regles d'association
- Export Top-K dans `top_k_products.csv`
- Export des correlations dans `footwear_correlations.csv`

## Etape 3: Kubeflow Pipelines

Le pipeline Kubeflow est defini dans `kubeflow_pipeline.py`.

Il contient trois composants:

1. `scrape_op`: execute `step1_web_scraper.py`
2. `enrich_op`: execute `step2_llm_enrichment.py`
3. `analyze_op`: execute `step3_ml_analytics.py`

Compiler le pipeline:

```powershell
python kubeflow_pipeline.py
```

Le fichier genere est:

```text
shoe_pipeline.yaml
```

Important: l'execution reelle dans Kubeflow necessite Kubernetes et Kubeflow Pipelines. Avec Docker seul, on peut generer le YAML mais pas executer Kubeflow.

## Etape 4: Dashboard BI

Le dashboard est implemente dans `step4_bi_dashboard.py`.

Fonctionnalites:

- KPIs globaux
- Produits Top Picks
- Tendances du marche
- Clusters de styles
- Intelligence par marque
- Exploration des donnees
- Analyse produit detaillee
- Hub d'insights AI
- Vue Responsible AI

Lancer le dashboard:

```powershell
streamlit run step4_bi_dashboard.py
```

## Etape 5: LLM enrichment

L'enrichissement est implemente dans `step2_llm_enrichment.py`.

Providers supportes:

- Google Gemini
- Groq

Attributs generes:

- `material`
- `sole_type`
- `closure`
- `gender`
- `short_description`
- `persona_json`

Les cles API sont configurees via `.env`.

## Etape 6: Responsible AI avec MCP-style server

Le fichier `step6_responsible_ai_mcp.py` expose un serveur MCP-style simplifie.

Principes appliques:

- Acces read-only aux donnees
- Liste blanche d'outils autorises
- Validation des parametres
- Limite maximale sur les resultats
- Journalisation dans `mcp_audit.log`
- Pas d'exposition directe de secrets

Outils exposes:

- `get_top_shoes`
- `analyze_cluster`
- `get_shop_ranking`

Tester:

```powershell
python step6_responsible_ai_mcp.py
```

## CI/CD

Le workflow GitHub Actions se trouve dans `.github/workflows/mlops.yml`.

Il effectue:

- Installation Python
- Installation des dependances
- Lancement MySQL 8.0
- Creation du schema via `schema.sql`
- Insertion de donnees test via `ci_seed.sql`
- Execution de `step3_ml_analytics.py`
- Compilation du pipeline Kubeflow
- Verification des artefacts generes

## Prerequis

- Python 3.10 ou 3.11
- MySQL 8.0 ou MariaDB compatible
- Docker optionnel
- Kubernetes requis uniquement pour executer Kubeflow reellement

## Installation locale

Creer un environnement Python:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Installer les dependances:

```powershell
pip install -r requirements.txt
```

Creer la base MySQL:

```sql
CREATE DATABASE smart_ecommerce;
```

Importer le schema:

```powershell
mysql -u root -p smart_ecommerce < schema.sql
```

Configurer `.env`:

```env
DB_HOST=localhost
DB_USER=root
DB_PASS=your_mysql_password
DB_NAME=smart_ecommerce
SHOP_INPUT_FILE=gulf_perfume_stores_shopify_woocommerce_verified.xlsx

GEMINI_KEYS=your_gemini_key
GROQ_KEYS=your_groq_key
```

## Execution locale

Lancer tout le pipeline local:

```powershell
python step5_mlops_pipeline.py
```

Ou lancer les etapes separement:

```powershell
python step1_web_scraper.py
python step2_llm_enrichment.py
python step3_ml_analytics.py
```

Lancer le dashboard:

```powershell
streamlit run step4_bi_dashboard.py
```

## Execution avec Docker

Construire l'image:

```powershell
docker build -t smart-shoe-pipeline:latest .
```

Si MySQL tourne sur la machine hote, utiliser dans `.env`:

```env
DB_HOST=host.docker.internal
```

Lancer le pipeline:

```powershell
docker run --env-file .env smart-shoe-pipeline:latest
```

## Kubeflow

Compiler le pipeline:

```powershell
python kubeflow_pipeline.py
```

Uploader `shoe_pipeline.yaml` dans Kubeflow Pipelines UI.

Pour une execution reelle, il faut:

- Kubernetes actif
- Kubeflow Pipelines installe
- Image `smart-shoe-pipeline:latest` disponible dans le cluster
- Acces reseau depuis les pods vers MySQL
- Variables d'environnement/secrets configures pour DB et LLM

## Artefacts generes

| Artefact | Description |
|---|---|
| `shoe_pipeline.yaml` | Pipeline Kubeflow compile |
| `top_k_products.csv` | Selection des meilleurs produits |
| `footwear_correlations.csv` | Regles d'association entre attributs footwear |
| `mcp_audit.log` | Logs d'acces aux outils MCP-style |

## Securite

- Ne jamais commiter `.env`.
- Ne jamais mettre de vraies cles API dans `.env.example`.
- Les cles Gemini/Groq doivent etre stockees localement ou dans des secrets CI/CD.
- Si une cle a deja ete publiee, elle doit etre revoquee et remplacee.

## Limites actuelles

- Le scraping dynamique JavaScript avec Selenium/Playwright n'est pas encore active.
- WooCommerce REST API n'est pas encore utilisee avec authentification officielle.
- Le pipeline Kubeflow necessite un environnement Kubernetes pour execution reelle.
- Les resultats ML dependent fortement de la qualite des donnees scrapees et enrichies.

## Commandes utiles

Verifier la syntaxe Python:

```powershell
python -m py_compile step1_web_scraper.py step2_llm_enrichment.py step3_ml_analytics.py step4_bi_dashboard.py step5_mlops_pipeline.py step6_responsible_ai_mcp.py kubeflow_pipeline.py
```

Compiler Kubeflow:

```powershell
python kubeflow_pipeline.py
```

Lancer le dashboard:

```powershell
streamlit run step4_bi_dashboard.py
```

Voir l'etat Git:

```powershell
git status
```
