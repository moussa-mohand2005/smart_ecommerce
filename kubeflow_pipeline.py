from kfp import dsl
from kfp import compiler

@dsl.component(base_image='python:3.10')
def scrape_op():
    import subprocess
    print("Starting Web Scraping Phase...")
    # In a real K8s environment, you'd have the code and dependencies in the image
    # subprocess.run(["python", "step1_web_scraper.py"], check=True)

@dsl.component(base_image='python:3.10')
def enrich_op():
    import subprocess
    print("Starting AI Enrichment Phase...")
    # subprocess.run(["python", "step2_llm_enrichment.py"], check=True)

@dsl.component(base_image='python:3.10')
def analyze_op():
    import subprocess
    print("Starting ML Analytics Phase...")
    # subprocess.run(["python", "step3_ml_analytics.py"], check=True)

@dsl.pipeline(
    name='Smart Shoe MLOps Pipeline',
    description='An end-to-end pipeline for shoe data scraping, AI enrichment, and ML analytics.'
)
def shoe_pipeline():
    scrape_task = scrape_op()
    enrich_task = enrich_op().after(scrape_task)
    analyze_task = analyze_op().after(enrich_task)

if __name__ == '__main__':
    compiler.Compiler().compile(
        pipeline_func=shoe_pipeline,
        package_path='shoe_pipeline.yaml'
    )
    print("Kubeflow Pipeline compiled to shoe_pipeline.yaml")
