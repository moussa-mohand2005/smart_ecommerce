import os
import json
import time
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
# Import libraries conditionally to avoid slow startups
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except:
    HAS_GEMINI = False

from groq import Groq
import pymysql
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEYS = [k.strip() for k in os.getenv("GEMINI_KEYS", "").split(",") if k.strip()]
GROQ_KEYS = [k.strip() for k in os.getenv("GROQ_KEYS", "").split(",") if k.strip()]

API_CONFIGS = []
for key in GEMINI_KEYS:
    API_CONFIGS.append({"provider": "gemini", "key": key, "model": "gemini-2.5-flash"})
for key in GROQ_KEYS:
    API_CONFIGS.append({"provider": "groq", "key": key, "model": "llama-3.1-8b-instant"})

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", ""),
        database=os.getenv("DB_NAME", "smart_ecommerce"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

# Thread-safe index for key rotation
class KeyRotator:
    def __init__(self, configs):
        self.configs = configs
        self.index = 0
        self.lock = threading.Lock()
    
    def get_next(self):
        with self.lock:
            config = self.configs[self.index]
            self.index = (self.index + 1) % len(self.configs)
            return config

rotator = KeyRotator(API_CONFIGS)

def call_llm(system_prompt, prompt):
    for _ in range(len(API_CONFIGS)):
        config = rotator.get_next()
        provider = config["provider"]
        api_key = config["key"]
        model_name = config["model"]
        try:
            text = ""
            if provider == "gemini" and HAS_GEMINI:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(system_prompt + "\n" + prompt)
                text = response.text
            elif provider == "groq":
                client = Groq(api_key=api_key)
                response = client.chat.completions.create(
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                    model=model_name, 
                    temperature=0.2,
                    response_format={"type": "json_object"} if "llama-3" in model_name else None
                )
                text = response.choices[0].message.content
            
            if "```json" in text: text = text.split("```json")[1].split("```")[0]
            elif "```" in text: text = text.split("```")[1].split("```")[0]
            return text.strip()
        except:
            # Silently continue to next key as requested
            continue
    return None

def enrich_batch(products):
    system_prompt = "Tu es un expert en mode et footwear spécialisé dans l'analyse de produits."
    prompt = """
    Je vais te donner une liste de chaussures avec leur nom et description.
    Pour chaque chaussure, extrais ces métriques techniques :
    1. Matière (Cuir, Mesh, Toile, Synthétique, etc.) -> 'material'
    2. Type de semelle (Gomme, Caoutchouc, Plateforme, etc.) -> 'sole_type'
    3. Type de fermeture (Lacets, Slip-on, Scratch, etc.) -> 'closure'
    4. Genre (homme, femme, enfant, unisexe, inconnu) -> 'gender'
    5. Une description courte en FRANÇAIS (max 120 caractères) -> 'short_description'

    Réponds UNIQUEMENT sous forme d'un objet JSON contenant une clé 'products' qui est un tableau d'objets.
    Chaque objet doit avoir les clés : id, material, sole_type, closure, gender, short_description.

    Produits :
    """
    for p in products:
        desc = (p['description_raw'] or 'N/A')[:500]
        prompt += f"\n- ID: {p['product_id']}, Nom: {p['product_name']}, Description: {desc}"

    result_text = call_llm(system_prompt, prompt)
    if result_text:
        try:
            data = json.loads(result_text)
            return data.get('products', data) if isinstance(data, dict) else data
        except:
            return None
    return None

def generate_persona(product):
    system_prompt = "Tu es un expert en marketing de mode. Réponds en JSON uniquement."
    prompt = f"Génère un profil client idéal pour : {product['product_name']} ({product.get('brand', '')}). Clés: nom_persona, age_cible, style_vie, traits_personnalite, occasion_port."
    res = call_llm(system_prompt, prompt)
    return res

def process_single_batch(batch, batch_id):
    print(f"[*] Processing Batch {batch_id} ({len(batch)} products)...")
    results = enrich_batch(batch)
    if not results:
        return False
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for res in results:
                try:
                    p_id = res.get('id')
                    gender = str(res.get('gender', 'inconnu')).lower()
                    if gender not in ['homme', 'femme', 'enfant', 'unisexe', 'inconnu']:
                        gender = 'inconnu'
                    
                    cur.execute("""
                        UPDATE products SET 
                            material=%s, sole_type=%s, closure=%s, 
                            gender=%s, short_description=%s, is_enriched=TRUE
                        WHERE product_id=%s
                    """, (
                        str(res.get('material', 'Inconnu')),
                        str(res.get('sole_type', 'Standard')),
                        str(res.get('closure', 'Inconnu')),
                        gender,
                        str(res.get('short_description', '')),
                        p_id
                    ))
                    
                    # Generate persona immediately for the enriched product
                    # To keep it efficient, we fetch the full row first
                    cur.execute("SELECT * FROM products WHERE product_id=%s", (p_id,))
                    p_data = cur.fetchone()
                    if p_data:
                        persona = generate_persona(p_data)
                        if persona:
                            cur.execute("UPDATE products SET persona_json=%s WHERE product_id=%s", (persona, p_id))
                except:
                    continue
            conn.commit()
    finally:
        conn.close()
    print(f"[+] Batch {batch_id} completed.")
    return True

def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT product_id, product_name, description_raw, brand FROM products WHERE is_enriched=FALSE")
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        print("No products to enrich.")
        return

    batch_size = 20
    batches = [rows[i:i+batch_size] for i in range(0, len(rows), batch_size)]
    print(f"--- Starting Parallel Enrichment (Total: {len(rows)} products, {len(batches)} batches) ---")
    
    # Use as many workers as keys to maximize throughput
    max_workers = max(1, len(API_CONFIGS))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_batch, b, i+1): i for i, b in enumerate(batches)}
        for future in as_completed(futures):
            try:
                future.result()
            except:
                pass

if __name__ == "__main__":
    main()

