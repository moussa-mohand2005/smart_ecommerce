from kfp import compiler, dsl


PIPELINE_IMAGE = "smart-shoe-pipeline:latest"


@dsl.component(base_image=PIPELINE_IMAGE)
def scrape_op():
    import subprocess
    import sys

    print("Starting Web Scraping Phase...")
    subprocess.run([sys.executable, "step1_web_scraper.py"], check=True)


@dsl.component(base_image=PIPELINE_IMAGE)
def enrich_op():
    import subprocess
    import sys

    print("Starting AI Enrichment Phase...")
    subprocess.run([sys.executable, "step2_llm_enrichment.py"], check=True)


@dsl.component(base_image=PIPELINE_IMAGE)
def analyze_op():
    import subprocess
    import sys

    print("Starting ML Analytics and Top-K Selection Phase...")
    subprocess.run([sys.executable, "step3_ml_analytics.py"], check=True)


@dsl.pipeline(
    name="Smart Shoe MLOps Pipeline",
    description="End-to-end scraping, LLM enrichment, ML scoring, and Top-K product selection."
)
def shoe_pipeline():
    scrape_task = scrape_op()
    enrich_task = enrich_op().after(scrape_task)
    analyze_op().after(enrich_task)


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=shoe_pipeline,
        package_path="shoe_pipeline.yaml"
    )
    print("Kubeflow Pipeline compiled to shoe_pipeline.yaml")
