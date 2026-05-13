import os
import json
import time
import sys
import threading
import requests as http_requests
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except:
    HAS_GEMINI = False

try:
    from groq import Groq
    HAS_GROQ = True
except:
    HAS_GROQ = False

import pymysql
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ────────────────────────────────────────────
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")

GEMINI_KEYS = [k.strip() for k in os.getenv("GEMINI_KEYS", "").split(",") if k.strip()]
GROQ_KEYS = [k.strip() for k in os.getenv("GROQ_KEYS", "").split(",") if k.strip()]

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", ""),
        database=os.getenv("DB_NAME", "smart_ecommerce"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

# ── Ollama (LOCAL - Primary) ────────────────────────────────
def call_ollama(system_prompt, prompt):
    """Call local Ollama model. No API key needed, no rate limits."""
    try:
        resp = http_requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": f"{system_prompt}\n\n{prompt}",
                "stream": False,
                "options": {"temperature": 0.2}
            },
            timeout=300
        )
        if resp.status_code == 200:
            text = resp.json().get("response", "")
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return text.strip()
    except Exception as e:
        print(f"  [Ollama Error] {e}")
    return None

# ── Cloud Fallbacks ──────────────────────────────────────────
def call_gemini(system_prompt, prompt, api_key):
    if not HAS_GEMINI:
        return None
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else api_key
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(system_prompt + "\n" + prompt)
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return text.strip()
    except Exception as e:
        error_msg = str(e).split("\n")[0][:100]  # Get first line and limit length
        print(f"  [⚠️ Gemini Key Error] Key ({masked_key}) failed: {error_msg}")
        return None

def call_groq(system_prompt, prompt, api_key):
    if not HAS_GROQ:
        return None
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else api_key
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        text = response.choices[0].message.content
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return text.strip()
    except Exception as e:
        error_msg = str(e).split("\n")[0][:100]  # Get first line and limit length
        print(f"  [⚠️ Groq Key Error] Key ({masked_key}) failed: {error_msg}")
        return None

def call_llm(system_prompt, prompt):
    """Try Groq first, then Gemini fallback, and Ollama as local fallback."""
    # 1. Groq (Primary)
    for key in GROQ_KEYS:
        result = call_groq(system_prompt, prompt, key)
        if result:
            return result

    # 2. Gemini fallback
    for key in GEMINI_KEYS:
        result = call_gemini(system_prompt, prompt, key)
        if result:
            return result

    # 3. Ollama fallback (local)
    result = call_ollama(system_prompt, prompt)
    if result:
        return result

    return None

# ── Enrichment Logic ─────────────────────────────────────────
def enrich_batch(products):
    system_prompt = "You are a fashion expert. Respond ONLY with valid JSON, no extra text."
    prompt = """I will give you fashion products. For each, extract:
1. material (Cotton, Polyester, Leather, Denim, etc.)
2. sole_type: For footwear=sole type (Rubber, Foam), For clothing=fit (Regular, Slim, Relaxed)
3. closure (Laces, Zip, Button, Pull-on, etc.)
4. gender (men, women, kids, unisex)
5. season (Spring, Summer, Fall, Winter, All-Season)
6. style_type (Casual, Formal, Athletic, Streetwear, etc.)
7. short_description (max 120 chars, English)

Respond as: {"products": [{"id": ..., "material": ..., "sole_type": ..., "closure": ..., "gender": ..., "season": ..., "style_type": ..., "short_description": ...}]}

Products:
"""
    for p in products:
        desc = (p['description_raw'] or 'N/A')[:200]
        prompt += f"\n- ID: {p['product_id']}, Name: {p['product_name']}, Category: {p.get('category','')}, Desc: {desc}"

    result_text = call_llm(system_prompt, prompt)
    if result_text:
        try:
            data = json.loads(result_text)
            return data.get('products', data) if isinstance(data, dict) else data
        except:
            return None
    return None

def generate_persona(product):
    system_prompt = "You are a fashion marketing expert. Respond ONLY with valid JSON."
    prompt = f"Generate an ideal customer profile for: {product['product_name']} ({product.get('brand','')}) in {product.get('category','')}. Keys: persona_name, target_age, lifestyle, personality_traits, wear_occasion."
    return call_llm(system_prompt, prompt)

def process_single_batch(batch, batch_id, total_batches):
    print(f"[*] Batch {batch_id}/{total_batches} ({len(batch)} products)...")
    results = enrich_batch(batch)
    if not results:
        print(f"  [!] Batch {batch_id} FAILED - no LLM response")
        return False

    conn = get_connection()
    updated = 0
    try:
        with conn.cursor() as cur:
            for res in results:
                try:
                    p_id = res.get('id')
                    gender = str(res.get('gender', 'unknown')).lower()
                    if gender not in ['men', 'women', 'kids', 'unisex', 'unknown']:
                        gender = 'unknown'

                    cur.execute("""
                        UPDATE products SET
                            material=%s, sole_type=%s, closure=%s,
                            gender=%s, season=%s, style_type=%s,
                            short_description=%s, is_enriched=TRUE
                        WHERE product_id=%s
                    """, (
                        str(res.get('material', 'Unknown')),
                        str(res.get('sole_type', 'Standard')),
                        str(res.get('closure', 'Unknown')),
                        gender,
                        str(res.get('season', 'All-Season')),
                        str(res.get('style_type', 'Casual')),
                        str(res.get('short_description', '')),
                        p_id
                    ))
                    updated += 1
                except:
                    continue
            conn.commit()
    finally:
        conn.close()
    print(f"  [+] Batch {batch_id} done ({updated} updated)")
    return True

def main():
    # Check Ollama connection
    try:
        r = http_requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        models = [m['name'] for m in r.json().get('models', [])]
        print(f"✅ Ollama connected. Models: {models}")
        if OLLAMA_MODEL not in models and not any(OLLAMA_MODEL in m for m in models):
            print(f"⚠️ Model '{OLLAMA_MODEL}' not found. Run: ollama pull {OLLAMA_MODEL}")
    except:
        print("⚠️ Ollama not available. Will try cloud APIs.")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT product_id, product_name, description_raw, brand, category FROM products WHERE is_enriched=FALSE")
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        print("No products to enrich.")
        return

    batch_size = 20  # Increased for faster processing
    batches = [rows[i:i+batch_size] for i in range(0, len(rows), batch_size)]
    print(f"--- Fashion Enrichment via Ollama ({len(rows)} products, {len(batches)} batches) ---")

    success = 0
    for i, batch in enumerate(batches):
        ok = process_single_batch(batch, i+1, len(batches))
        if ok:
            success += 1

    print(f"\n--- Done. {success}/{len(batches)} batches succeeded ---")

if __name__ == "__main__":
    main()
