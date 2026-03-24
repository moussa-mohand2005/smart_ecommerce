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
from dotenv import load_dotenv

load_dotenv()


try:
    import google.generativeai as genai
    HAS_GEMINI = True
except:
    HAS_GEMINI = False

from groq import Groq

MAX_PRODUCTS = 500
total_inserted = 0
counter_lock = threading.Lock()
stop_event = threading.Event()

GEMINI_KEYS = [k.strip() for k in os.getenv("GEMINI_KEYS", "").split(",") if k.strip()]
GROQ_KEYS = [k.strip() for k in os.getenv("GROQ_KEYS", "").split(",") if k.strip()]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1"
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
                print(f"      [DEBUG AI] Model: {config['model']} | Response: {res_text} | Msg: {prompt[:50]}...")
                return res_text
            elif config["provider"] == "groq":
                client = Groq(api_key=config["key"])
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=config["model"],
                    temperature=0.1
                )
                res_text = response.choices[0].message.content.strip().upper()
                print(f"      [DEBUG AI] Model: {config['model']} | Response: {res_text} | Product: {prompt[:50]}...")
                return res_text
        except: continue
    return "UNKNOWN"

def is_footwear_ai(name, description=""):
    prompt = f"Product: {name}\nDesc: {(description or '')[:150]}\nQuestion: Is this a shoe, boot, sandal, or sneaker? Answer ONLY 'YES' or 'NO'."
    answer = call_llm_simple(prompt)
    if "YES" in answer: return True
    return False

def is_footwear(name, description=""):
    text = (str(name) + " " + str(description)).lower()
    
    EXCLUSIONS = [
        'sock', 't-shirt', 'tee', 'hoodie', 'pant', 'short', 'bag', 'hat', 'cap', 'accessory', 
        'belt', 'wallet', 'cleaning kit', 'lace', 'shirt', 'jacket', 'coat', 'jewelry', 'socks',
        'hoody', 'sweatshirt', 'backpack', 'beanie', 'gloves', 'scarf', 'sunglasses', 'hood',
        'sweat', 'jogger', 'legging', 'top', 'blouse', 'dress', 'skirt', 'jewelry', 'watch'
    ]
    
    INCLUSIONS = [
        'shoe', 'sneaker', 'boot', 'sandal', 'heel', 'loafer', 'clog', 'mule', 'flat', 
        'pump', 'oxford', 'derby', 'brogue', 'chelsea', 'chukka', 'espadrille', 
        'flip flop', 'slide', 'trainer', 'footwear', 'slipper', 'allbirds', 'veja',
        'koio', 'taft', 'clarks', 'ecco', 'steve madden', 'aldo', 'greats', 'cariuma',
        'nisolo', 'axel arigato', 'filling pieces', 'oliver cabell', 'thursday boots',
        'wolf & shepherd', 'common projects', 'rothys', 'beckett simonon', 'on running'
    ]
    
    return any(re.search(r'\b' + re.escape(inc) + r'\b', text) for inc in INCLUSIONS)

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", ""),
        database=os.getenv("DB_NAME", "smart_ecommerce"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

def get_or_create_shop(shop_name, shop_url, platform):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT shop_id FROM shops WHERE shop_name=%s LIMIT 1", (shop_name,))
            row = cur.fetchone()
            if row:
                return row["shop_id"]
            
            sql = "INSERT INTO shops (shop_name, platform, shop_url) VALUES (%s, %s, %s)"
            cur.execute(sql, (shop_name, platform, shop_url))
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()

def fetch_content(url, is_json=False):
    for attempt in range(3):
        user_agent = random.choice(USER_AGENTS)
        headers = {"User-Agent": user_agent, "Accept": "application/json" if is_json else "text/html,application/xhtml+xml"}
        try:
            time.sleep(random.uniform(1.5, 3.0))
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                return response.json() if is_json else response.text
            elif response.status_code == 403:
                print(f"  [!] 403 Forbidden for {url}")
            elif response.status_code == 429:
                print(f"  [!] 429 Too Many Requests. Sleeping...")
                time.sleep(10)
        except Exception as e:
            print(f"  [!] Error fetching {url}: {e}")
    return None

def scrape_shopify_sitemap(shop_url):
    sitemap_url = urljoin(shop_url, "/sitemap_products_1.xml")
    html = fetch_content(sitemap_url)
    if not html: return []
    
    # Simple regex to find <loc> tags in XML
    import re
    locs = re.findall(r"<loc>(https?://[^<]+)</loc>", html)
    product_links = [l for l in locs if "/products/" in l]
    print(f"  [+] Found {len(product_links)} product links in sitemap.")
    return product_links

def detect_platform(html, url):
    if not html: return "other"
    html_lower = html.lower()
    if "shopify" in html_lower or "/products/" in url or "cdn.shopify.com" in html:
        return "shopify"
    if "woocommerce" in html_lower or "wp-content" in html_lower or "/product/" in url or "wc-ajax" in html_lower:
        return "woocommerce"
    if 'type-product' in html_lower or 'woocommerce-product-gallery' in html_lower:
        return "woocommerce"
    return "other"

def scrape_shopify_json(shop_url, shop_id, brand_name):
    products = []
    for page in range(1, 101):
        json_url = urljoin(shop_url, f"/products.json?limit=250&page={page}")
        data = fetch_content(json_url, is_json=True)
        if not data or 'products' not in data or not data['products']: break
        
        print(f"    [Page {page}] Found {len(data['products'])} items...")
        for p in data['products']:
            if stop_event.is_set(): break
            
            # Filter: Basic Regex first, then AI
            if not is_footwear(p['title'], p.get('body_html', '')):
                continue
            
            # Second check: AI Verification
            if not is_footwear_ai(p['title'], p.get('body_html', '')):
                print(f"      [AI Filter] Skipped non-shoe: {p['title']}")
                continue

            variants = p.get('variants', [{}])
            first_variant = variants[0]
            p_url = urljoin(shop_url, f"/products/{p['handle']}")

            products.append({
                "external_product_id": str(p['id']),
                "shop_id": shop_id,
                "product_url": p_url,
                "category": "Shoes",
                "subcategory": "Sneakers",
                "brand": brand_name,
                "product_name": p['title'],
                "description_raw": BeautifulSoup(p.get('body_html', ''), "html.parser").get_text(" ", strip=True),
                "current_price": float(first_variant.get('price', 0)),
                "currency": "AED",
                "rating_avg": None,
                "reviews_count": 0,
                "stock_status": "in_stock" if first_variant.get('available', True) else "out_of_stock",
                "image_url_main": p['images'][0]['src'] if p.get('images') else None
            })
    return products

def extract_product_links(collection_url, base_url, platform):
    html = fetch_content(collection_url)
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    pattern = "/products/" if platform == "shopify" else "/product/"
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if pattern in href:
            full_url = urljoin(base_url, href.split("?")[0])
            links.add(full_url)
    return sorted(links)

def parse_product_page(url, shop_id, brand_name, platform):
    html = fetch_content(url)
    if not html: return None
    soup = BeautifulSoup(html, "html.parser")
    
    import json
    product_data = {}
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, list): data = data[0]
            if data.get("@type") == "Product" or "Product" in str(data.get("@type")):
                product_data = data
                break
        except: continue

    if product_data:
        title = product_data.get("name")
        price = product_data.get("offers", {}).get("price")
        if not price and isinstance(product_data.get("offers"), list):
            price = product_data["offers"][0].get("price")
        img_url = product_data.get("image")
        if isinstance(img_url, list): img_url = img_url[0]
        desc = product_data.get("description", "")
    else:
        # Fallback to standard scraping
        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else None
        if not title:
            og = soup.find("meta", attrs={"property": "og:title"})
            title = og["content"].strip() if og else None

        price = None
        price_meta = soup.find("meta", attrs={"property": "product:price:amount"})
        if price_meta: 
            try: price = float(price_meta["content"])
            except: pass
        
        img = soup.find("meta", attrs={"property": "og:image"})
        img_url = img["content"] if img else None
        desc = "" # Will fill from description_raw

            desc = soup.body.get_text(" ", strip=True) if soup.body else ""

    # Determine stock status
    stock_status = "unknown"
    if product_data.get("offers", {}).get("availability") == "http://schema.org/InStock":
        stock_status = "in_stock"
    elif product_data.get("offers", {}).get("availability") == "http://schema.org/OutOfStock":
        stock_status = "out_of_stock"
    elif "add to cart" in html.lower() or "in stock" in html.lower():
        stock_status = "in_stock"
    elif "out of stock" in html.lower():
        stock_status = "out_of_stock"

    data = {
        "external_product_id": url.rstrip("/").split("/")[-1],
        "shop_id": shop_id,
        "product_url": url,
        "category": "Shoes",
        "subcategory": "Sneakers",
        "brand": brand_name,
        "product_name": title,
        "description_raw": desc[:1000], # Truncate description
        "current_price": price,
        "currency": "AED",
        "rating_avg": None,
        "reviews_count": 0,
        "stock_status": stock_status,
        "image_url_main": img_url
    }
    
    if title and is_footwear(title, desc):
        if is_footwear_ai(title, desc):
            return data
        else:
            print(f"      [AI Filter] Skipped non-shoe: {title}")
    return None

def process_shop(row):
    if stop_event.is_set(): return
    site_url, collection_url = row['site_url'], row['women_collection_url']
    if pd.isna(site_url) or pd.isna(collection_url): return
    
    shop_name = row.get('shop_name')
    if pd.isna(shop_name) or not shop_name:
        shop_name = urlparse(site_url).netloc.replace("www.", "").split(".")[0].capitalize()
    
    print(f"[*] Processing: {shop_name}...")
    
    try:
        html_home = fetch_content(site_url)
        platform = detect_platform(html_home, site_url)
        shop_id = get_or_create_shop(shop_name, site_url, platform)
        
        products = []
        
        if platform == "shopify":
            api_products = scrape_shopify_json(site_url, shop_id, shop_name)
            if api_products:
                products = api_products
                print(f"  [+] Found {len(api_products)} products via JSON API")
        
        if not products and platform == "shopify":
            links = scrape_shopify_sitemap(site_url)
            for link in links[:1000]: 
                if stop_event.is_set(): break
                p = parse_product_page(link, shop_id, shop_name, platform)
                if p: products.append(p)
            if products:
                print(f"  [+] Extracted {len(products)} products via Sitemap")

            for link in links[:1000]: 
                if stop_event.is_set(): break
                p = parse_product_page(link, shop_id, shop_name, platform)
                if p and p['product_name']:
                    products.append(p)
            if products:
                print(f"  [+] Extracted {len(products)} products via HTML Crawl")

        for p in products:
            if stop_event.is_set(): break
            insert_product(p)
            
    except Exception as e:
        print(f"  [!] Error {shop_name}: {e}")

def insert_product(product):
    global total_inserted
    
    with counter_lock:
        if total_inserted >= MAX_PRODUCTS:
            stop_event.set()
            return
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            sql = """
            INSERT INTO products (
                external_product_id, shop_id, product_url, category, subcategory, brand,
                product_name, description_raw, current_price, currency, rating_avg, 
                reviews_count, stock_status, image_url_main, scraped_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            cur.execute(sql, (
                product["external_product_id"], product["shop_id"], product["product_url"],
                product["category"], product["subcategory"], product["brand"],
                product["product_name"], product["description_raw"], product["current_price"],
                product["currency"], product["rating_avg"], product["reviews_count"],
                product["stock_status"], product["image_url_main"]
            ))
            
            with counter_lock:
                total_inserted += 1
                if total_inserted % 10 == 0:
                    print(f"  [Progress] {total_inserted}/{MAX_PRODUCTS} products collected...")
                if total_inserted >= MAX_PRODUCTS:
                    print(f"!!! LIMIT REACHED: {MAX_PRODUCTS} products collected. Stopping... !!!")
                    stop_event.set()
        conn.commit()
    except Exception as e:
        # print(f"Error inserting: {e}")
        pass
    finally: conn.close()

def main():
    try: 
        df = pd.read_excel(r"c:\Users\LENOVO\Downloads\pro fenan\code\gulf_perfume_stores_shopify_woocommerce_verified.xlsx")
    except Exception as e: 
        print(f"Error loading Excel: {e}")
        return
    
    print(f"--- Starting Smart AI Scraper (Target: {MAX_PRODUCTS} shoes) ---")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_shop, row) for _, row in df.iterrows()]
        for future in as_completed(futures):
            if stop_event.is_set():
                break
            future.result()
    
    print(f"--- Finished. Total collected: {total_inserted} ---")

if __name__ == "__main__":
    main()
