import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Smart Shoe | Business Intelligence",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Outfit:wght@300;400;600&display=swap');
    :root {
        --dark-bg: #0a0e0c;
        --surface-1: #0d1210;
        --surface-2: #121815;
        --gold-bright: #d4af37;
        --gold-dim: #997a25;
        --gold-border: rgba(212, 175, 55, 0.2);
        --text-primary: #e8f4f2;
        --text-secondary: #7a9e98;
    }
    .stApp { background-color: var(--dark-bg); color: var(--text-primary); font-family: 'Outfit', sans-serif; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3.2rem; background: linear-gradient(135deg, #f0e68c 0%, #d4af37 50%, #997a25 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.02em; margin-bottom: 0.5rem; }
    .section-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.25em; color: var(--gold-dim); margin-bottom: 2rem; display: block; }
    .stTabs [data-baseweb="tab-list"] { background: var(--surface-1); border-radius: 50px; padding: 5px; gap: 10px; border: 1px solid var(--gold-border); }
    .stTabs [data-baseweb="tab"] { background: transparent; border: none; color: var(--text-secondary); padding: 10px 25px; border-radius: 40px; transition: 0.4s; font-size: 0.85rem; }
    .stTabs [aria-selected="true"] { background: var(--gold-bright) !important; color: #000 !important; font-weight: 600; box-shadow: 0 4px 15px rgba(212,175,55,0.3); }
    div[data-testid="stMetricValue"] { font-family: 'Playfair Display', serif; color: var(--gold-bright); font-size: 1.8rem; }
</style>
""", unsafe_allow_html=True)

def theme(fig, title=None):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Outfit", color="#7a9e98", size=11),
        title=dict(text=title, font=dict(family="Playfair Display", size=18, color="#d4af37"), x=0.5) if title else None,
        margin=dict(t=60, b=40, l=40, r=40),
        xaxis=dict(gridcolor="rgba(46,158,138,0.08)", zeroline=False),
        yaxis=dict(gridcolor="rgba(46,158,138,0.08)", zeroline=False),
    )
GOLD_SCALE = [[0, "#0d1210"], [0.2, "#1a6657"], [1, "#d4af37"]]

def get_data():
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", ""),
        database=os.getenv("DB_NAME", "smart_ecommerce"),
        charset="utf8mb4"
    )
    df = pd.read_sql("SELECT * FROM products", conn)
    conn.close()
    return df

try:
    df = get_data()
    df['current_price'] = pd.to_numeric(df['current_price'], errors='coerce').fillna(0)
    df['rating_avg'] = pd.to_numeric(df['rating_avg'], errors='coerce').fillna(0)
    df['ml_score'] = pd.to_numeric(df['ml_score'], errors='coerce').fillna(0)
    df['reviews_count'] = pd.to_numeric(df['reviews_count'], errors='coerce').fillna(0)
    df['cluster_id'] = df['cluster_id'].fillna(0).astype(int)
    
    df['score_tier'] = pd.cut(df['ml_score'], bins=[0, 40, 60, 75, 90, 100], labels=["Standard", "Premium", "Excellence", "Imperial", "Masterpiece"])
    df['price_band'] = pd.cut(df['current_price'], bins=[0, 50, 100, 200, 500, 10000], labels=["Under $50", "$50-$100", "$100-$200", "$200-$500", "$500+"])
    df['value_index'] = df['ml_score'] / (df['current_price'] + 1)
    
    # New: Ensure PCA and Persona columns exist
    for col in ['pca_x', 'pca_y', 'persona_json', 'predicted_success']:
        if col not in df.columns: df[col] = None
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

st.markdown('<h1 class="main-title">E-COMMERCE INTELLIGENCE</h1>', unsafe_allow_html=True)
st.markdown('<span class="section-label">Luxury Footwear Catalog Analytics</span>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Shoe Hunt Filters")
    brands = sorted(df['brand'].unique())
    selected_brands = st.multiselect("Select Brands", brands, default=[])
    price_range = st.slider("Price Range", 0, int(df['current_price'].max()), (0, int(df['current_price'].max())))
    min_score = st.slider("Minimum Smart Score", 0, 100, 0)
    
filtered_df = df.copy()
if selected_brands: filtered_df = filtered_df[filtered_df['brand'].isin(selected_brands)]
filtered_df = filtered_df[(filtered_df['current_price'] >= price_range[0]) & (filtered_df['current_price'] <= price_range[1])]
filtered_df = filtered_df[filtered_df['ml_score'] >= min_score]

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1: st.metric("Unique Items", len(df))
with k2: st.metric("Avg Score", f"{df['ml_score'].mean():.1f}")
with k3: st.metric("Total Brands", df['brand'].nunique())
with k4: st.metric("Luxury (90+)", len(df[df['ml_score'] >= 90]))
with k5: st.metric("Price Median", f"${df['current_price'].median():.0f}")
in_stock = len(df[df['stock_status'].astype(str).str.lower().str.contains("instock", na=False)])
with k6: st.metric("In Stock", in_stock)

st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Top Picks", "Market Analysis", "Style Clusters", "Customer Personas", "Brand Intelligence", "Data Explorer", "AI Insight Hub", "Agent Reflection (MCP)"
])

with tab1:
    st.markdown('<h2 style="font-size:1.35rem; margin-bottom:1rem; font-weight:400;">Curated Footwear Collection</h2>', unsafe_allow_html=True)
    top_picks = filtered_df.nlargest(min(12, len(filtered_df)), "ml_score")
    cols = st.columns(3)
    for idx, (_, row) in enumerate(top_picks.iterrows()):
        stock_color = "#5a9e78" if "instock" in str(row['stock_status']).lower() else "#b85a4a"
        img_tag = f'<img src="{row["image_url_main"]}" style="width:100%; height:180px; object-fit:cover; border-radius:8px; margin-bottom:1rem; border: 1px solid rgba(212,175,55,0.1);">' if row["image_url_main"] else '<div style="width:100%; height:180px; background:#1a1a1a; border-radius:8px; margin-bottom:1rem; display:flex; align-items:center; justify-content:center; color:#3a5450;">No Image</div>'
        
        with cols[idx % 3]:
            st.markdown(f"""
            <div style="background:#121a17; border:1px solid rgba(46,158,138,0.25); border-radius:12px; padding:1.2rem; margin-bottom:1.5rem; transition: 0.3s; box-shadow: 0 4px 20px rgba(0,0,0,0.4);">
                {img_tag}
                <div style="font-size:0.58rem; letter-spacing:0.16em; text-transform:uppercase; color:#d4af37; margin-bottom:0.3rem;">{row['brand']}</div>
                <div style="font-family:'Playfair Display',serif; font-size:1.1rem; color:#e8f4f2; margin-bottom:0.75rem; line-height:1.2; min-height:2.6rem;">{row['product_name']}</div>
                <div style="height:3px; background:rgba(46,158,138,0.1); border-radius:3px; margin-bottom:0.8rem;">
                    <div style="height:3px; width:{int(row['ml_score'])}%; background:linear-gradient(90deg,#d4af37,#997a25); border-radius:3px;"></div>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:1.2rem; font-weight:600; color:#e8f4f2;">${row['current_price']:.0f}</span>
                    <span style="background:rgba(212,175,55,0.1); border:1px solid rgba(212,175,55,0.3); color:#d4af37; padding:2px 12px; border-radius:20px; font-size:0.7rem; font-weight:600;">AI {row['ml_score']:.1f}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-top:0.8rem; font-size:0.7rem; color:#7a9e98;">
                    <span>Rating {row['rating_avg']:.1f} ⭐</span><span style="color:{stock_color}; font-weight:600;">{row['stock_status'].upper()}</span>
                </div>
            </div>""", unsafe_allow_html=True)

with tab2:
    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.scatter(filtered_df, x="current_price", y="ml_score", size="reviews_count", color="cluster_id", hover_name="product_name", color_continuous_scale=GOLD_SCALE)
        theme(fig, "Price vs Score Distribution")
        st.plotly_chart(fig, width="stretch")
    with col_b:
        pstats = filtered_df.groupby("price_band", observed=True).agg(Count=("product_id","count"), Avg_Score=("ml_score","mean")).reset_index()
        fig2 = go.Figure([go.Bar(x=pstats["price_band"].astype(str), y=pstats["Count"], name="Products", marker_color="#0f3028")])
        fig2.add_trace(go.Scatter(x=pstats["price_band"].astype(str), y=pstats["Avg_Score"], name="Avg Score", mode="lines+markers", line=dict(color="#7ecfcc"), yaxis="y2"))
        fig2.update_layout(yaxis2=dict(overlaying="y", side="right", gridcolor="rgba(0,0,0,0)"))
        theme(fig2, "Products by Price Band")
        st.plotly_chart(fig2, width="stretch")

with tab3:
    col_t1, col_t2 = st.columns([1, 2])
    with col_t1:
        ccounts = df.groupby("cluster_id").size().reset_index(name="count")
        fig_p = go.Figure(go.Pie(labels=ccounts["cluster_id"].astype(str), values=ccounts["count"], hole=0.55, marker=dict(colors=["#2e9e8a","#1a6657","#7ecfcc","#5abf9e","#b85a4a"])))
        theme(fig_p, "Catalog Composition")
        st.plotly_chart(fig_p, width="stretch")
    with col_t2:
        if df['pca_x'].notnull().any():
            fig_pca = px.scatter(filtered_df, x="pca_x", y="pca_y", color="cluster_id", hover_name="product_name", 
                                 title="AI-Generated Style Map (PCA)", color_continuous_scale=GOLD_SCALE)
            theme(fig_pca)
            st.plotly_chart(fig_pca, width="stretch")
        else:
            cland = df.groupby("cluster_id").agg(Avg_Score=("ml_score","mean"), Count=("product_id","count")).reset_index()
            fig_r = go.Figure(go.Scatterpolar(r=cland["Avg_Score"], theta=cland["cluster_id"].astype(str), fill="toself", line=dict(color="#2e9e8a")))
            theme(fig_r, "Style Score Landscape")
            st.plotly_chart(fig_r, width="stretch")

with tab4:
    st.markdown('<h2 style="font-size:1.35rem; margin-bottom:1rem; font-weight:400;">Target Audience Insights</h2>', unsafe_allow_html=True)
    import json
    p_with_persona = filtered_df[filtered_df['persona_json'].notnull()].head(6)
    if p_with_persona.empty:
        st.info("No persona data available. Run Enrichment Agent to generate profiling.")
    else:
        pcols = st.columns(2)
        for i, (_, row) in enumerate(p_with_persona.iterrows()):
            try:
                per = json.loads(row['persona_json'])
                with pcols[i%2]:
                    st.markdown(f"""
                    <div style="background:#121815; border:1px solid rgba(212,175,55,0.1); border-radius:8px; padding:1.5rem; margin-bottom:1rem;">
                        <div style="color:#d4af37; font-size:1.1rem; margin-bottom:0.5rem;">{per.get('nom_persona', 'Indéfini')}</div>
                        <div style="font-size:0.8rem; color:#7a9e98; margin-bottom:1rem;">
                            <b>Audience:</b> {per.get('age_cible', 'N/A')} | <b>Style:</b> {per.get('style_vie', 'N/A')}<br>
                            <b>Produit:</b> {row['product_name']}
                        </div>
                        <div style="font-size:0.75rem; border-left:2px solid #d4af37; padding-left:10px; color:#e8f4f2;">
                            <i>"{per.get('traits_personnalite', '')}"</i>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            except: pass
    bstats = df.groupby("brand").agg(Products=("product_id","count"), Avg_Score=("ml_score","mean"), Avg_Price=("current_price","mean"), Total_Reviews=("reviews_count","sum")).round(2).reset_index()
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        top_b = bstats.nlargest(12, "Avg_Score")
        fig_b1 = px.bar(top_b, x="Avg_Score", y="brand", orientation="h", color="Avg_Score", color_continuous_scale=GOLD_SCALE)
        theme(fig_b1, "Brand Quality Ranking")
        st.plotly_chart(fig_b1, width="stretch")
    with col_b2:
        fig_b2 = px.scatter(bstats, x="Avg_Price", y="Avg_Score", size="Products", color="Avg_Score", color_continuous_scale=GOLD_SCALE)
        theme(fig_b2, "Brand Positioning Map")
        st.plotly_chart(fig_b2, width="stretch")
    st.markdown("---")
    st.markdown("### 🧬 Footwear Attribute Correlations")
    try:
        rules = pd.read_csv("footwear_correlations.csv")
        st.dataframe(rules[['antecedents', 'consequents', 'lift']].head(10), width="stretch", hide_index=True)
    except: st.info("Run ML Analysis to see correlations.")

with tab6:
    st.dataframe(filtered_df, width="stretch", hide_index=True, column_config={
        "image_url_main": st.column_config.ImageColumn("Preview", help="Product Image"),
        "product_url": st.column_config.LinkColumn("Link"),
        "ml_score": st.column_config.ProgressColumn("Smart Score", min_value=0, max_value=100, format="%.1f"),
    })

with tab7:
    st.markdown("### Strategic Market Intelligence")
    if st.button("✨ Generate AI Report"):
        from groq import Groq
        api_keys = os.getenv("GROQ_KEYS", "").split(",")
        if api_keys and api_keys[0]:
            client = Groq(api_key=api_keys[0])
            summary = f"Products: {len(df)}, Avg Score: {df['ml_score'].mean():.1f}, Top Brand: {bstats.nlargest(1,'Avg_Score')['brand'].values[0]}"
            try:
                resp = client.chat.completions.create(messages=[{"role":"system","content":"Tu es un expert luxe. Analyse: "},{"role":"user","content":summary}], model="llama-3.1-8b-instant")
                st.markdown(f'<div style="background:#121815; padding:2rem; border-radius:12px; border:1px solid rgba(212,175,55,0.2);">{resp.choices[0].message.content}</div>', unsafe_allow_html=True)
            except Exception as e: st.error(f"AI Error: {e}")

with tab8:
    st.markdown("### Responsible AI Architecture (MCP)")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown("- **Decoupled Tools**: Tools isolation.\n- **Audit**: Logged execution.\n- **Ethical Isolation**: No direct SQL.")
    with col_m2:
        from step6_responsible_ai_mcp import ShoeMCPServer
        server = ShoeMCPServer()
        st.json(server.list_tools())
        if st.button("Simulate Responsible Call"):
            st.success("Tool Execution Validated")
            st.write(server.call_tool("get_top_shoes", {"limit": 2}))

st.markdown("""<div style="text-align:center; padding:2rem 0; font-size:0.6rem; color:#2a2520; text-transform:uppercase; letter-spacing:0.2em;">Smart Shoe — BI Platform</div>""", unsafe_allow_html=True)