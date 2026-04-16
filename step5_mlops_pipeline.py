import subprocess
import sys

def run_step(step_name, script_name):
    print(f"\n{'='*60}")
    print(f"🚀 Running {step_name} ({script_name})...")
    print(f"{'='*60}")
    try:
        subprocess.run([sys.executable, script_name], check=True)
        print(f"✅ {step_name} completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {step_name}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def main():
    print("\n" + "*"*60)
    print("      SMART SHOE INTELLIGENCE - MLOps MASTER PIPELINE      ")
    print("*"*60)
    
    run_step("Data Scraping & Collection", "step1_web_scraper.py")
    run_step("LLM Enrichment (Gemini/Groq)", "step2_llm_enrichment.py")
    run_step("ML Data Analytics", "step3_ml_analytics.py")
    
    print("\n" + "="*60)
    print("🎉 ALL PHASES COMPLETED SUCCESSFULLY!")
    print("🚀 You can now run: 'streamlit run step4_bi_dashboard.py'")
    print("="*60)

if __name__ == "__main__":
    main()
