import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pymysql
import re
import pandas as pd
import sys
import os
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except:
    HAS_GEMINI = False

from groq import Groq

MAX_PRODUCTS = 5000
total_inserted = 0
counter_lock = threading.Lock()
stop_event = threading.Event()

GEMINI_KEYS = [k.strip() for k in os.getenv("GEMINI_KEYS", "").split(",") if k.strip()]
GROQ_KEYS = [k.strip() for k in os.getenv("GROQ_KEYS", "").split(",") if k.strip()]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1"
]

API_CONFIGS = []
for key in GEMINI_KEYS:
    API_CONFIGS.append({"provider": "gemini", "key": key, "model": "gemini-2.0-flash"})
for key in GROQ_KEYS:
    API_CONFIGS.append({"provider": "groq", "key": key, "model": "llama-3.3-70b-versatile"})

class KeyRotator:
    def __init__(self, configs):
        self.configs = configs
        self.index = 0
        self.lock = threading.Lock()
    def get_next(self):
        with self.lock:
            if not self.configs: return None
            config = self.configs[self.index]
            self.index = (self.index + 1) % len(self.configs)
            return config

rotator = KeyRotator(API_CONFIGS)

def call_llm_simple(prompt):
    for _ in range(len(API_CONFIGS)):
        config = rotator.get_next()
        if not config: break
        try:
            if config["provider"] == "gemini" and HAS_GEMINI:
                genai.configure(api_key=config["key"])
                model = genai.GenerativeModel(config["model"])
                response = model.generate_content(prompt)
                res_text = response.text.strip().upper()
                return res_text
            elif config["provider"] == "groq":
                client = Groq(api_key=config["key"])
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=config["model"], temperature=0.1
                )
                res_text = response.choices[0].message.content.strip().upper()
                return res_text
        except: continue
    return "UNKNOWN"

def is_fashion_ai(name, description=""):
    prompt = f"Product: {name}\nDesc: {(description or '')[:150]}\nIs this clothing or footwear? Answer ONLY 'YES' or 'NO'."
    answer = call_llm_simple(prompt)
    return "YES" in answer

def is_fashion(name, description=""):
    text = (str(name) + " " + str(description)).lower()
    EXCLUSIONS = ['gift card','e-gift','sticker','phone case','poster','mug','candle',
                  'keychain','dog collar','pet','supplement','vitamin','protein powder',
                  'shaker','bottle','yoga mat','resistance band','foam roller','cleaning kit']
    INCLUSIONS = [
        'shoe','sneaker','boot','sandal','heel','loafer','clog','mule','flat','pump',
        'oxford','derby','slipper','slide','trainer','footwear','espadrille','flip flop',
        'shirt','t-shirt','tee','polo','blouse','tank top','crop top','hoodie','sweatshirt',
        'sweater','cardigan','pullover','jacket','coat','blazer','vest','parka','windbreaker',
        'pants','jeans','trousers','shorts','skirt','legging','jogger','chinos','cargo',
        'dress','gown','jumpsuit','romper','bodysuit','underwear','boxer','bra','bralette',
        'sock','lingerie','shapewear','bikini','swimsuit','swimwear','activewear','sportswear',
        'hat','cap','beanie','scarf','gloves','belt','tie','sunglasses',
    ]
    if any(re.search(r'\b' + re.escape(e) + r'\b', text) for e in EXCLUSIONS):
        return False
    return any(re.search(r'\b' + re.escape(i) + r'\b', text) for i in INCLUSIONS)

def guess_category(title, desc="", ptype=""):
    text = (str(title) + " " + str(desc) + " " + str(ptype)).lower()
    fw = ['shoe','sneaker','boot','sandal','heel','loafer','clog','mule','flat','pump',
          'oxford','derby','slipper','slide','trainer','footwear','espadrille']
    category = "Footwear" if any(k in text for k in fw) else "Clothing"
    sc_map = {
        'sneaker':'Sneakers','trainer':'Sneakers','boot':'Boots','sandal':'Sandals',
        'slide':'Slides','heel':'Heels','pump':'Heels','loafer':'Loafers','oxford':'Oxfords',
        'slipper':'Slippers','clog':'Clogs','flat':'Flats',
        't-shirt':'T-Shirts','tee':'T-Shirts','shirt':'Shirts','polo':'Polos',
        'hoodie':'Hoodies','sweatshirt':'Sweatshirts','sweater':'Sweaters',
        'jacket':'Jackets','coat':'Coats','blazer':'Blazers','vest':'Vests',
        'pants':'Pants','jean':'Jeans','shorts':'Shorts','skirt':'Skirts',
        'legging':'Leggings','jogger':'Joggers','dress':'Dresses','jumpsuit':'Jumpsuits',
        'romper':'Rompers','bodysuit':'Bodysuits','bikini':'Swimwear','swimsuit':'Swimwear',
        'bra':'Bras','underwear':'Underwear','sock':'Socks','lingerie':'Lingerie',
    }
    subcategory = "General"
    for kw, sc in sc_map.items():
        if kw in text: subcategory = sc; break
    if any(w in text for w in ['women','woman','ladies','femme','girls']): gender = "women"
    elif any(w in text for w in ['men','man','guys','homme','boys']): gender = "men"
    elif any(w in text for w in ['kid','child','junior','youth','baby']): gender = "kids"
    else: gender = "unisex"
    return category, subcategory, gender

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST","localhost"), user=os.getenv("DB_USER","root"),
        password=os.getenv("DB_PASS",""), database=os.getenv("DB_NAME","smart_ecommerce"),
        charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)

def get_or_create_shop(shop_name, shop_url, platform):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT shop_id FROM shops WHERE shop_name=%s LIMIT 1", (shop_name,))
            row = cur.fetchone()
            if row: return row["shop_id"]
            cur.execute("INSERT INTO shops (shop_name, platform, shop_url) VALUES (%s,%s,%s)",
                        (shop_name, platform, shop_url))
            conn.commit()
            return cur.lastrowid
    finally: conn.close()

def fetch_content(url, is_json=False):
    for attempt in range(3):
        headers = {"User-Agent": random.choice(USER_AGENTS),
                   "Accept": "application/json" if is_json else "text/html,application/xhtml+xml"}
        try:
            time.sleep(random.uniform(0.3, 0.8))
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200: return r.json() if is_json else r.text
            elif r.status_code == 429: time.sleep(10)
        except: pass
    return None

def scrape_shopify_sitemap(shop_url):
    html = fetch_content(urljoin(shop_url, "/sitemap_products_1.xml"))
    if not html: return []
    locs = re.findall(r"<loc>(https?://[^<]+)</loc>", html)
    links = [l for l in locs if "/products/" in l]
    print(f"  [+] Found {len(links)} product links in sitemap.")
    return links

def detect_platform(html, url):
    if not html: return "other"
    h = html.lower()
    if "shopify" in h or "cdn.shopify.com" in html: return "shopify"
    if "woocommerce" in h or "wp-content" in h or "wc-ajax" in h: return "woocommerce"
    return "other"

def scrape_shopify_json(shop_url, shop_id, brand_name):
    products = []
    for page in range(1, 101):
        data = fetch_content(urljoin(shop_url, f"/products.json?limit=250&page={page}"), is_json=True)
        if not data or 'products' not in data or not data['products']: break
        print(f"    [Page {page}] Found {len(data['products'])} items...")
        for p in data['products']:
            if stop_event.is_set(): break
            title = p['title']; body = p.get('body_html',''); ptype = p.get('product_type','')
            if not is_fashion(title, body): continue
            v = p.get('variants',[{}])[0]
            cat, subcat, gender = guess_category(title, body, ptype)
            products.append({
                "external_product_id": str(p['id']), "shop_id": shop_id,
                "product_url": urljoin(shop_url, f"/products/{p['handle']}"),
                "category": cat, "subcategory": subcat, "brand": brand_name,
                "product_name": title,
                "description_raw": BeautifulSoup(body,"html.parser").get_text(" ",strip=True),
                "current_price": float(v.get('price',0)), "currency": "USD",
                "rating_avg": None, "reviews_count": 0,
                "stock_status": "in_stock" if v.get('available',True) else "out_of_stock",
                "image_url_main": p['images'][0]['src'] if p.get('images') else None
            })
    return products

def extract_product_links(collection_url, base_url, platform):
    html = fetch_content(collection_url)
    if not html: return []
    soup = BeautifulSoup(html,"html.parser")
    pattern = "/products/" if platform == "shopify" else "/product/"
    links = set()
    for a in soup.find_all("a", href=True):
        if pattern in a["href"]:
            links.add(urljoin(base_url, a["href"].split("?")[0]))
    return sorted(links)

def parse_product_page(url, shop_id, brand_name, platform):
    html = fetch_content(url)
    if not html: return None
    soup = BeautifulSoup(html,"html.parser")
    import json as _json
    pd_data = {}
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            d = _json.loads(s.string)
            if isinstance(d, list): d = d[0]
            if "Product" in str(d.get("@type","")): pd_data = d; break
        except: continue
    if pd_data:
        title = pd_data.get("name"); price = pd_data.get("offers",{}).get("price")
        if not price and isinstance(pd_data.get("offers"),list): price = pd_data["offers"][0].get("price")
        img = pd_data.get("image"); img = img[0] if isinstance(img,list) else img
        desc = pd_data.get("description","")
    else:
        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else None
        if not title:
            og = soup.find("meta", attrs={"property":"og:title"})
            title = og["content"].strip() if og else None
        price = None
        pm = soup.find("meta", attrs={"property":"product:price:amount"})
        if pm:
            try: price = float(pm["content"])
            except: pass
        im = soup.find("meta", attrs={"property":"og:image"})
        img = im["content"] if im else None
        desc = soup.body.get_text(" ",strip=True) if soup.body else ""
    stock = "unknown"
    avail = pd_data.get("offers",{}).get("availability","")
    if "InStock" in avail: stock = "in_stock"
    elif "OutOfStock" in avail: stock = "out_of_stock"
    elif "add to cart" in html.lower(): stock = "in_stock"
    cat, subcat, gender = guess_category(title or "", desc, "")
    data = {
        "external_product_id": url.rstrip("/").split("/")[-1], "shop_id": shop_id,
        "product_url": url, "category": cat, "subcategory": subcat, "brand": brand_name,
        "product_name": title, "description_raw": desc[:1000], "current_price": price,
        "currency": "USD", "rating_avg": None, "reviews_count": 0,
        "stock_status": stock, "image_url_main": img
    }
    if title and is_fashion(title, desc):
        return data
    return None

def process_shop(row):
    if stop_event.is_set(): return
    site_url = row['site_url']
    collection_url = row.get('collection_url','')
    if pd.isna(site_url): return
    if pd.isna(collection_url): collection_url = ''
    shop_name = row.get('shop_name')
    if pd.isna(shop_name) or not shop_name:
        shop_name = urlparse(site_url).netloc.replace("www.","").split(".")[0].capitalize()
    print(f"[*] Processing: {shop_name}...")
    try:
        html_home = fetch_content(site_url)
        platform = detect_platform(html_home, site_url)
        shop_id = get_or_create_shop(shop_name, site_url, platform)
        products = []
        if platform == "shopify":
            products = scrape_shopify_json(site_url, shop_id, shop_name)
            if products: print(f"  [+] Found {len(products)} products via JSON API")
        if not products and platform == "shopify":
            links = scrape_shopify_sitemap(site_url)
            for link in links[:1000]:
                if stop_event.is_set(): break
                p = parse_product_page(link, shop_id, shop_name, platform)
                if p: products.append(p)
            if products: print(f"  [+] Extracted {len(products)} via Sitemap")
        if not products and collection_url:
            links = extract_product_links(collection_url, site_url, platform)
            for link in links[:1000]:
                if stop_event.is_set(): break
                p = parse_product_page(link, shop_id, shop_name, platform)
                if p and p['product_name']: products.append(p)
            if products: print(f"  [+] Extracted {len(products)} via HTML Crawl")
        for p in products:
            if stop_event.is_set(): break
            insert_product(p)
    except Exception as e:
        print(f"  [!] Error {shop_name}: {e}")

def insert_product(product):
    global total_inserted
    with counter_lock:
        if total_inserted >= MAX_PRODUCTS: stop_event.set(); return
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
            INSERT INTO products (
                external_product_id, shop_id, product_url, category, subcategory, brand,
                product_name, description_raw, current_price, currency, rating_avg,
                reviews_count, stock_status, image_url_main, scraped_at
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
            """, (
                product["external_product_id"], product["shop_id"], product["product_url"],
                product["category"], product["subcategory"], product["brand"],
                product["product_name"], product["description_raw"], product["current_price"],
                product["currency"], product["rating_avg"], product["reviews_count"],
                product["stock_status"], product["image_url_main"]
            ))
            with counter_lock:
                total_inserted += 1
                if total_inserted % 50 == 0:
                    print(f"  [Progress] {total_inserted}/{MAX_PRODUCTS} products collected...")
                if total_inserted >= MAX_PRODUCTS:
                    print(f"!!! LIMIT REACHED: {MAX_PRODUCTS} products collected. Stopping... !!!")
                    stop_event.set()
        conn.commit()
    except: pass
    finally: conn.close()

def main():
    input_file = Path(os.getenv("SHOP_INPUT_FILE","fashion_stores_shopify_woocommerce.xlsx"))
    try: df = pd.read_excel(input_file)
    except Exception as e: print(f"Error loading Excel '{input_file}': {e}"); return
    print(f"--- Starting Smart Fashion AI Scraper (Target: {MAX_PRODUCTS} products) ---")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_shop, row) for _, row in df.iterrows()]
        for f in as_completed(futures):
            if stop_event.is_set(): break
            f.result()
    print(f"--- Finished. Total collected: {total_inserted} ---")

if __name__ == "__main__":
    main()
