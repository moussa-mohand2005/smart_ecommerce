import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px
import plotly.graph_objects as go
import os
import json
from dotenv import load_dotenv
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

load_dotenv()

st.set_page_config(
    page_title="Smart Shoe BI",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
@import url('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css');

:root {
    --bg:        #0f172a;
    --side:      #1e293b;
    --card:      #1e293b;
    --card-h:    #334155;
    --border:    rgba(255,255,255,0.08);
    --accent:    #0ea5e9;
    --accent-h:  #38bdf8;
    --indigo:    #6366f1;
    --success:   #22c55e;
    --text:      #f8fafc;
    --muted:     #94a3b8;
    --glass:     rgba(30, 41, 59, 0.7);
}

/* Base */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, sans-serif;
    color: var(--text);
}
.stApp { background: var(--bg); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { display: none; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--side) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebarContent"] { padding: 1.5rem 1rem; }

/* Sidebar branding */
.sb-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0 0 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.sb-logo-icon {
    width: 40px; height: 40px;
    background: linear-gradient(135deg, var(--accent), var(--indigo));
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    color: white;
}
.sb-logo-text {
    font-weight: 800;
    font-size: 1.25rem;
    color: var(--text);
    letter-spacing: -0.02em;
}
.sb-logo-sub {
    font-size: 0.65rem;
    color: var(--muted);
    letter-spacing: 0.05em;
    text-transform: uppercase;
    font-weight: 600;
}

/* Section label in sidebar */
.sb-section {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 1.5rem 0 0.75rem 0.5rem;
}

/* Metric cards */
.kpi-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.25rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
.kpi-card:hover {
    border-color: var(--accent);
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
}
.kpi-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--muted);
    margin-bottom: 0.5rem;
}
.kpi-value {
    font-size: 1.85rem;
    font-weight: 800;
    color: var(--text);
    line-height: 1.1;
}
.kpi-value.accent { color: var(--accent); }
.kpi-sub {
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 0.5rem;
    display: flex; align-items: center; gap: 4px;
}

/* Page title */
.page-title {
    font-size: 2.25rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    color: var(--text);
    line-height: 1.1;
    margin-bottom: 0.5rem;
}
.page-sub {
    font-size: 0.85rem;
    color: var(--muted);
    letter-spacing: 0.05em;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 2rem;
}

/* Navigation in Sidebar */
.stRadio > div {
    gap: 6px;
}
.stRadio label {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    margin-bottom: 6px !important;
    font-size: 0.82rem !important;
    transition: all 0.2s ease;
}
.stRadio label:hover {
    background: rgba(14,165,233,0.1) !important;
    border-color: var(--accent) !important;
}
.stRadio label div[data-testid="stMarkdownContainer"] p {
    color: #94a3b8 !important;
}
.stRadio div[role="radiogroup"] > div[data-checked="true"] label {
    background: rgba(14,165,233,0.15) !important;
    border-color: var(--accent) !important;
}
.stRadio div[role="radiogroup"] > div[data-checked="true"] label p {
    color: var(--accent) !important;
    font-weight: 700 !important;
}

/* Expanders */
.stExpander {
    border: none !important;
    background: transparent !important;
    margin-bottom: 0.5rem !important;
}
.stExpander summary {
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    color: var(--muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}
.stExpander summary:hover {
    color: var(--accent) !important;
}

/* Product cards */
.prod-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1rem;
    margin-bottom: 1rem;
    transition: all 0.25s;
    position: relative;
    overflow: hidden;
}
.prod-card:hover {
    border-color: rgba(61,255,192,0.2);
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.4);
}
.prod-img {
    width: 100%; height: 170px;
    object-fit: cover;
    border-radius: 10px;
    margin-bottom: 0.85rem;
    border: 1px solid var(--border);
}
.prod-img-empty {
    width: 100%; height: 170px;
    background: var(--card2);
    border-radius: 10px;
    margin-bottom: 0.85rem;
    display: flex; align-items: center; justify-content: center;
    color: var(--muted); font-size: 0.75rem;
}
.prod-brand {
    font-size: 0.6rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.3rem;
}
.prod-name {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.4;
    margin-bottom: 1rem;
    min-height: 2.8rem;
}
.prod-bar-bg {
    height: 4px;
    background: var(--card-h);
    border-radius: 4px;
    margin-bottom: 1rem;
}
.prod-bar-fill {
    height: 4px;
    border-radius: 4px;
    background: var(--accent);
}
.prod-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.prod-price {
    font-size: 1.25rem;
    font-weight: 800;
    color: var(--text);
}
.prod-badge {
    font-size: 0.7rem;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 8px;
    background: rgba(14, 165, 233, 0.1);
    color: var(--accent);
}
.prod-meta {
    display: flex;
    justify-content: space-between;
    margin-top: 0.75rem;
    font-size: 0.75rem;
    color: var(--muted);
}
.stock-in  { color: var(--success); font-weight: 600; }
.stock-out { color: var(--danger); font-weight: 600; }

/* Section heading */
.section-heading {
    font-size: 1.2rem;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 12px;
    letter-spacing: -0.01em;
}
.section-heading::before {
    content: '';
    display: inline-block;
    width: 4px; height: 20px;
    background: var(--accent);
    border-radius: 2px;
}

/* ── Persona card ── */
/* Table */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid var(--border); }

/* Divider */
hr { border-color: var(--border) !important; }

/* ── Streamlit overrides ── */
/* ── Streamlit overrides ── */
div[data-testid="stMetricValue"] { color: var(--accent) !important; font-weight: 800 !important; }
.stSelectbox > div, .stMultiSelect > div { background: var(--card) !important; border-color: var(--border) !important; border-radius: 10px !important; }
.stSlider > div > div > div { background: var(--accent) !important; }
label[data-testid="stWidgetLabel"] { color: var(--muted) !important; font-size: 0.8rem !important; font-weight: 600 !important; }

/* Button */
.stButton > button {
    background: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    color: white !important;
    border-radius: 10px !important;
    padding: 0.5rem 1.5rem !important;
    font-weight: 700 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: var(--accent-h) !important;
    border-color: var(--accent-h) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3) !important;
}
</style>
""", unsafe_allow_html=True)

ACCENT_COLOR = "#0ea5e9"
INDIGO_COLOR = "#6366f1"
ACCENT_SCALE = ["#0f172a", "#1e293b", "#0ea5e9", "#6366f1"]

def apply_theme(fig, title=None, height=360):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=height,
        font=dict(family="Inter, sans-serif", color="#94a3b8", size=12),
        title=dict(
            text=title,
            font=dict(size=16, color="#f8fafc", weight="bold"),
            x=0.02, xanchor="left"
        ) if title else None,
        margin=dict(t=60 if title else 20, b=40, l=20, r=20),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0, font=dict(size=11)),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=False, tickfont=dict(size=10)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=False, tickfont=dict(size=10)),
    )
    return fig

def card_wrap(content, padding="1.2rem 1.4rem"):
    return f"""<div style="background:#131918;border:1px solid rgba(255,255,255,0.06);
    border-radius:14px;padding:{padding};margin-bottom:1rem;">{content}</div>"""

@st.cache_data(ttl=300)
def get_data():
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", ""),
        database=os.getenv("DB_NAME", "smart_ecommerce"),
        charset="utf8mb4",
    )
    df = pd.read_sql("SELECT * FROM products", conn)
    conn.close()
    return df

try:
    df = get_data()
    for col in ['current_price', 'rating_avg', 'ml_score', 'reviews_count']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['cluster_id'] = df['cluster_id'].fillna(0).astype(int)
    for col in ['pca_x', 'pca_y', 'persona_json', 'predicted_success']:
        if col not in df.columns:
            df[col] = None

    df['score_tier'] = pd.cut(df['ml_score'], bins=[0,40,60,75,90,100],
        labels=["Standard","Premium","Excellence","Imperial","Masterpiece"])
    df['price_band'] = pd.cut(df['current_price'], bins=[0,50,100,200,500,10000],
        labels=["<$50","$50–100","$100–200","$200–500","$500+"])
    df['value_index'] = df['ml_score'] / (df['current_price'] + 1)
except Exception as e:
    st.error(f"⚠️ Database connection failed: {e}")
    st.stop()

with st.sidebar:
    st.markdown("""
    <div class="sb-logo">
        <div class="sb-logo-icon"><i class="bi bi-layers-half"></i></div>
        <div>
            <div class="sb-logo-text">Smart Shoe</div>
            <div class="sb-logo-sub">BI Platform</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-section" style="margin-top:0.5rem;">Main Navigation</div>', unsafe_allow_html=True)
    menu_options = [
        "Curated Top Picks",
        "Market Trends",
        "Style Clusters",
        "Brand Intelligence",
        "Data Explorer",
        "AI Insight Hub",
        "Responsible AI"
    ]
    selected_page = st.radio("Navigation", menu_options, label_visibility="collapsed")

    st.markdown('<div class="sb-section" style="margin-top:2rem;">Intelligence Filters</div>', unsafe_allow_html=True)

    with st.expander("🌍 Market Segments", expanded=False):
        brands = sorted(df['brand'].dropna().unique())
        selected_brands = st.multiselect("Active Brands", brands, placeholder="Select brands")
        price_min, price_max = int(df['current_price'].min()), int(df['current_price'].max())
        price_range = st.slider("Price Threshold ($)", price_min, price_max, (price_min, price_max))

    with st.expander("🧬 Technical Traits", expanded=False):
        min_score = st.slider("Minimum AI Score", 0, 100, 0)
        clusters = sorted(df['cluster_id'].unique())
        selected_clusters = st.multiselect("Style Clusters", [str(c) for c in clusters], placeholder="All clusters")
        show_instock = st.checkbox("In stock only", value=False)

# Sidebar Footer Metrics
    st.markdown("<div style='flex-grow:1'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.02); border-radius:12px; padding:1rem; border:1px solid rgba(255,255,255,0.05);">
        <div style="font-size:0.65rem; color:var(--muted); text-transform:uppercase; margin-bottom:0.8rem; letter-spacing:1px;">Data Index Status</div>
        <div style="font-size:0.75rem; color:var(--text); line-height:2;">
            <i class="bi bi-cpu" style="color:var(--accent);"></i>&nbsp; Assets: <b>{len(df)}</b><br>
            <i class="bi bi-tag" style="color:var(--indigo);"></i>&nbsp; Labels: <b>{df['brand'].nunique()}</b><br>
            <i class="bi bi-diagram-3" style="color:var(--accent);"></i>&nbsp; Groups: <b>{df['cluster_id'].nunique()}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

fdf = df.copy()
if selected_brands:
    fdf = fdf[fdf['brand'].isin(selected_brands)]
fdf = fdf[(fdf['current_price'] >= price_range[0]) & (fdf['current_price'] <= price_range[1])]
fdf = fdf[fdf['ml_score'] >= min_score]
if selected_clusters:
    fdf = fdf[fdf['cluster_id'].isin([int(c) for c in selected_clusters])]
if show_instock:
    fdf = fdf[fdf['stock_status'].astype(str).str.lower().str.contains("instock", na=False)]

in_stock_count = len(df[df['stock_status'].astype(str).str.lower().str.contains("instock", na=False)])
masterpiece_count = len(df[df['ml_score'] >= 90])
active_filters_count = len(fdf)

if selected_page == "Curated Top Picks":
    header_col, _ = st.columns([3, 1])
    with header_col:
        st.markdown('<div class="page-title">Smart Ecommerce</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-sub">Enterprise Asset Management & AI Valuation</div>', unsafe_allow_html=True)

    kpis = [
        ("Inventory Volume", f"{len(df):,}", "accent", f"{len(fdf):,} Active"),
        ("Collective Score", f"{df['ml_score'].mean():.1f}", "accent", "out of 100"),
        ("Market Diversity", f"{df['brand'].nunique()}", "accent", "Vetted Brands"),
        ("Masterpiece Tier", f"{masterpiece_count}", "accent", "Score 90+"),
        ("Valuation Median", f"${df['current_price'].median():.0f}", "accent", "Global Avg"),
        ("Active Stock", f"{in_stock_count}", "accent", f"{in_stock_count/len(df)*100:.0f}% Fulfillment"),
    ]

    cols = st.columns(6)
    for col, (label, value, cls, sub) in zip(cols, kpis):
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value {cls}">{value}</div>
                <div class="kpi-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-heading"><i class="bi bi-award"></i>&nbsp; Curated Top Picks</div>', unsafe_allow_html=True)

    sort_col, n_col, _ = st.columns([2, 2, 4])
    with sort_col:
        sort_by = st.selectbox("Sort by", ["AI Score", "Price ↑", "Price ↓", "Rating", "Reviews"], label_visibility="visible")
    with n_col:
        n_items = st.selectbox("Show", [6, 9, 12, 24], index=1)

    sort_map = {
        "AI Score": ("ml_score", False),
        "Price ↑": ("current_price", True),
        "Price ↓": ("current_price", False),
        "Rating": ("rating_avg", False),
        "Reviews": ("reviews_count", False),
    }
    s_col, s_asc = sort_map[sort_by]
    top_picks = fdf.nlargest(n_items, s_col) if not s_asc else fdf.nsmallest(n_items, s_col)

    if top_picks.empty:
        st.info("No products match your filters.")
    else:
        cols = st.columns(3)
        for idx, (_, row) in enumerate(top_picks.iterrows()):
            in_s = "instock" in str(row['stock_status']).lower()
            stock_cls = "stock-in" if in_s else "stock-out"
            stock_lbl = "● IN STOCK" if in_s else "● OUT OF STOCK"
            img_html = (
                f'<img src="{row["image_url_main"]}" class="prod-img">'
                if row.get("image_url_main")
                else '<div class="prod-img-empty">No Image</div>'
            )
            with cols[idx % 3]:
                st.markdown(f"""
                <div class="prod-card">
                    {img_html}
                    <div class="prod-brand">{row['brand']}</div>
                    <div class="prod-name">{row['product_name']}</div>
                    <div class="prod-bar-bg">
                        <div class="prod-bar-fill" style="width:{int(row['ml_score'])}%;"></div>
                    </div>
                    <div class="prod-footer">
                        <span class="prod-price">${row['current_price']:.0f}</span>
                        <span class="prod-badge">AI {row['ml_score']:.1f}</span>
                    </div>
                    <div class="prod-meta">
                        <span>⭐ {row['rating_avg']:.1f} &nbsp;·&nbsp; {int(row['reviews_count'])} reviews</span>
                        <span class="{stock_cls}">{stock_lbl}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

elif selected_page == "Market Trends":
    st.markdown('<div class="section-heading"><i class="bi bi-graph-up-arrow"></i>&nbsp; Market Trends Overview</div>', unsafe_allow_html=True)

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        fig = px.scatter(
            fdf, x="current_price", y="ml_score",
            size="reviews_count", color="cluster_id",
            hover_name="product_name",
            color_continuous_scale=ACCENT_SCALE,
            labels={"current_price": "Price ($)", "ml_score": "AI Score"},
        )
        apply_theme(fig, "Price vs AI Score")
        st.plotly_chart(fig, use_container_width=True)

    with r1c2:
        pstats = fdf.groupby("price_band", observed=True).agg(
            Count=("product_id", "count"),
            Avg_Score=("ml_score", "mean")
        ).reset_index()
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=pstats["price_band"].astype(str), y=pstats["Count"],
            name="# Products", marker_color="rgba(14, 165, 233, 0.2)",
            marker_line_width=0,
        ))
        fig2.add_trace(go.Scatter(
            x=pstats["price_band"].astype(str), y=pstats["Avg_Score"],
            name="Avg Score", mode="lines+markers",
            line=dict(color="#6366f1", width=3),
            marker=dict(size=8, color="#6366f1", line=dict(color="white", width=1.5)),
            yaxis="y2"
        ))
        fig2.update_layout(
            yaxis2=dict(overlaying="y", side="right", gridcolor="rgba(0,0,0,0)", color="#5e7d75"),
            legend=dict(orientation="h", y=1.08),
        )
        apply_theme(fig2, "Price Band Distribution")
        st.plotly_chart(fig2, use_container_width=True)

    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1:
        tier_counts = fdf['score_tier'].value_counts().reset_index()
        fig3 = px.pie(
            tier_counts, names='score_tier', values='count', hole=0.6,
            color_discrete_sequence=["#1e293b", "#0f172a", "#0ea5e9", "#6366f1", "#8b5cf6"],
        )
        apply_theme(fig3, "Score Tier Distribution")
        st.plotly_chart(fig3, use_container_width=True)

    with r2c2:
        fig4 = px.histogram(
            fdf, x="ml_score", nbins=20,
            color_discrete_sequence=["#3dffc0"],
            labels={"ml_score": "AI Score"},
        )
        fig4.update_traces(marker_line_width=0, opacity=0.85)
        apply_theme(fig4, "Score Distribution")
        st.plotly_chart(fig4, use_container_width=True)

    with r2c3:
        fig5 = px.scatter(
            fdf, x="rating_avg", y="ml_score",
            color="current_price", color_continuous_scale=ACCENT_SCALE,
            hover_name="product_name",
            labels={"rating_avg": "Rating", "ml_score": "AI Score"},
        )
        apply_theme(fig5, "Rating vs AI Score")
        st.plotly_chart(fig5, use_container_width=True)

elif selected_page == "Style Clusters":
    st.markdown('<div class="section-heading"><i class="bi bi-grid-3x3-gap"></i>&nbsp; AI-Generated Clusters</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2])
    with c1:
        ccounts = fdf.groupby("cluster_id").size().reset_index(name="count")
        fig_p = go.Figure(go.Pie(
            labels=["Cluster " + str(x) for x in ccounts["cluster_id"]],
            values=ccounts["count"],
            hole=0.6,
            marker=dict(colors=["#0f6b4f","#1aaa82","#3dffc0","#e8c55a","#b8ffd9","#ff9f6b"]),
            textinfo="percent",
        ))
        apply_theme(fig_p, "Cluster Composition")
        st.plotly_chart(fig_p, use_container_width=True)

        cstats = fdf.groupby("cluster_id").agg(
            Avg_Score=("ml_score","mean"),
            Avg_Price=("current_price","mean"),
            Count=("product_id","count"),
        ).round(1).reset_index()
        st.dataframe(
            cstats,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Avg_Score": st.column_config.ProgressColumn("Avg Score", min_value=0, max_value=100, format="%.1f"),
            }
        )

    with c2:
        if fdf['pca_x'].notnull().any():
            fig_pca = px.scatter(
                fdf, x="pca_x", y="pca_y",
                color="cluster_id", hover_name="product_name",
                color_continuous_scale=ACCENT_SCALE,
                labels={"pca_x": "PCA 1", "pca_y": "PCA 2"},
            )
            apply_theme(fig_pca, "Style Map (PCA 2D Projection)", height=420)
            st.plotly_chart(fig_pca, use_container_width=True)
        else:
            cland = fdf.groupby("cluster_id").agg(
                Avg_Score=("ml_score","mean"),
                Avg_Price=("current_price","mean"),
                Avg_Rating=("rating_avg","mean"),
            ).reset_index()
            theta_cats = ["Avg Score","Avg Price","Avg Rating","Avg Score"]
            fig_r = go.Figure()
            colors = ["#0ea5e9", "#6366f1", "#8b5cf6", "#ec4899", "#f43f5e"]
            for i, row in cland.iterrows():
                norm_score = row['Avg_Score']
                norm_price = min(row['Avg_Price'] / 500 * 100, 100)
                norm_rating = row['Avg_Rating'] / 5 * 100
                vals = [norm_score, norm_price, norm_rating, norm_score]
                fig_r.add_trace(go.Scatterpolar(
                    r=vals, theta=theta_cats,
                    fill="toself", name=f"Cluster {row['cluster_id']}",
                    line=dict(color=colors[i % len(colors)], width=2),
                ))
            fig_r.update_layout(polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickcolor="#64748b", color="#64748b"),
                angularaxis=dict(gridcolor="rgba(255,255,255,0.06)", color="#64748b"),
            ))
            apply_theme(fig_r, "Cluster Radar Profile", height=420)
            st.plotly_chart(fig_r, use_container_width=True)

elif selected_page == "Brand Intelligence":
    st.markdown('<div class="section-heading"><i class="bi bi-bookmark-star"></i>&nbsp; Brand Intelligence</div>', unsafe_allow_html=True)

    bstats = df.groupby("brand").agg(
        Products=("product_id","count"),
        Avg_Score=("ml_score","mean"),
        Avg_Price=("current_price","mean"),
        Total_Reviews=("reviews_count","sum"),
    ).round(2).reset_index()

    b1, b2 = st.columns(2)
    with b1:
        top_b = bstats.nlargest(15, "Avg_Score")
        fig_b1 = px.bar(
            top_b, x="Avg_Score", y="brand", orientation="h",
            color="Avg_Score", color_continuous_scale=ACCENT_SCALE,
            labels={"Avg_Score": "Avg AI Score", "brand": ""},
        )
        fig_b1.update_traces(marker_line_width=0)
        apply_theme(fig_b1, "Brand Quality Ranking", height=420)
        st.plotly_chart(fig_b1, use_container_width=True)

    with b2:
        fig_b2 = px.scatter(
            bstats, x="Avg_Price", y="Avg_Score",
            size="Products", color="Avg_Score",
            hover_name="brand",
            color_continuous_scale=ACCENT_SCALE,
            labels={"Avg_Price": "Avg Price ($)", "Avg_Score": "Avg AI Score"},
        )
        apply_theme(fig_b2, "Brand Positioning Map", height=420)
        st.plotly_chart(fig_b2, use_container_width=True)

    st.markdown('<div class="section-heading">Brand Comparison Table</div>', unsafe_allow_html=True)
    st.dataframe(
        bstats.sort_values("Avg_Score", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Avg_Score": st.column_config.ProgressColumn("Avg AI Score", min_value=0, max_value=100, format="%.1f"),
            "Avg_Price": st.column_config.NumberColumn("Avg Price", format="$%.0f"),
            "Total_Reviews": st.column_config.NumberColumn("Reviews", format="%d"),
        }
    )

    st.markdown('<div class="section-heading" style="margin-top:1.5rem;">🧬 Footwear Attribute Correlations</div>', unsafe_allow_html=True)
    try:
        rules = pd.read_csv("footwear_correlations.csv")
        st.dataframe(
            rules[['antecedents','consequents','lift']].head(10),
            use_container_width=True, hide_index=True
        )
    except:
        st.info("Run ML Analysis to generate attribute correlation rules.")

elif selected_page == "Data Explorer":
    if 'detail_view_id' not in st.session_state:
        st.session_state.detail_view_id = None

    if st.session_state.detail_view_id:
        p_id = st.session_state.detail_view_id
        product = df[df['product_id'] == p_id].iloc[0]
        
        top_c1, top_c2 = st.columns([5, 1])
        with top_c1:
            st.markdown(f'<div class="page-title">{product["product_name"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="page-sub">{product["brand"]} · Asset Intelligence Profile</div>', unsafe_allow_html=True)
        with top_c2:
            if st.button("⬅ Back to Gallery", use_container_width=True):
                st.session_state.detail_view_id = None
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        hero_left, hero_right = st.columns([1, 1.4])
        with hero_left:
            st.image(product['image_url_main'], use_container_width=True)
        
        with hero_right:
            st.markdown('<div class="section-heading"><i class="bi bi-file-earmark-bar-graph"></i>&nbsp; Executive Summary</div>', unsafe_allow_html=True)
            
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("AI Score", f"{product['ml_score']:.1f}", delta=f"Tier: High" if product['ml_score'] >= 70 else "Tier: Mid")
            k2.metric("Success Prob.", f"{product.get('predicted_success',0):.1f}%")
            k3.metric("Rating", f"{product['rating_avg']:.1f} ⭐")
            k4.metric("Unit Price", f"${product['current_price']:.0f}")

            st.markdown('<div class="section-heading" style="margin-top:2rem;"><i class="bi bi-sliders"></i>&nbsp; Technical Profile</div>', unsafe_allow_html=True)
            t1, t2, t3, t4 = st.columns(4)
            profiles = [
                ("Material", product['material'], "bi-cpu"),
                ("Sole Type", product['sole_type'], "bi-exclude"),
                ("Closure", product['closure'], "bi-lock-fill"),
                ("Target", product['gender'], "bi-people-fill")
            ]
            for col, (label, val, icon) in zip([t1, t2, t3, t4], profiles):
                col.markdown(f"""
                <div style="background:rgba(255,255,255,0.03); border-radius:12px; padding:1rem; text-align:center;">
                    <div style="font-size:0.7rem; color:var(--muted); text-transform:uppercase; margin-bottom:0.5rem; letter-spacing:1px;">{label}</div>
                    <i class="bi {icon}" style="font-size:1.2rem; color:var(--accent);"></i>
                    <div style="font-size:0.85rem; font-weight:700; color:var(--text); margin-top:0.5rem;">{val}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        m_left, m_right = st.columns([1, 1])
        
        with m_left:
            st.markdown('<div class="section-heading"><i class="bi bi-geo-alt"></i>&nbsp; Market Positioning Analysis</div>', unsafe_allow_html=True)
            cid = product['cluster_id']
            cluster_data = df[df['cluster_id'] == cid]
            
            st.markdown(f"""
            <div style="background:var(--card); border:1px solid var(--border); border-radius:16px; padding:1.5rem; margin-bottom:1rem;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.2rem;">
                    <span style="font-size:0.85rem; color:var(--muted);">Product vs Style Group <b>(Cluster {cid})</b></span>
                    <span style="background:rgba(14,165,233,0.1); color:var(--accent); padding:4px 10px; border-radius:20px; font-size:0.7rem; font-weight:800; text-transform:uppercase;">Group: {len(cluster_data)} Items</span>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1.5rem;">
                    <div>
                        <div style="font-size:0.65rem; color:var(--muted); margin-bottom:4px;">QUALITY RANK</div>
                        <div style="font-size:1.4rem; font-weight:800; color:var(--text); font-family:'Inter',sans-serif;">#{cluster_data['ml_score'].rank(ascending=False).iloc[0]:.0f}</div>
                        <div style="font-size:0.75rem; color:var(--accent);">Top {(cluster_data['ml_score'].rank(ascending=False).iloc[0] / len(cluster_data) * 100):.0f}% of cluster</div>
                    </div>
                    <div>
                        <div style="font-size:0.65rem; color:var(--muted); margin-bottom:4px;">PRICE INDEX</div>
                        <div style="font-size:1.4rem; font-weight:800; color:var(--text); font-family:'Inter',sans-serif;">{ (product['current_price'] / (cluster_data['current_price'].mean() or 1) * 100):.0f}%</div>
                        <div style="font-size:0.75rem; color:var(--muted);">of cluster average</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            avg_score = cluster_data['ml_score'].mean()
            avg_price = min(cluster_data['current_price'].mean()/5, 100)
            avg_rating = cluster_data['rating_avg'].mean()*20
            
            theta_cats = ["Quality Score", "Price Index", "User Rating", "Quality Score"]
            fig_p = go.Figure()
            fig_p.add_trace(go.Scatterpolar(
                r=[avg_score, avg_price, avg_rating, avg_score],
                theta=theta_cats, fill="toself", name="Cluster Avg",
                line=dict(color="rgba(255,255,255,0.2)", width=1), fillcolor="rgba(255,255,255,0.05)"
            ))
            fig_p.add_trace(go.Scatterpolar(
                r=[product['ml_score'], min(product['current_price']/5, 100), product['rating_avg']*20, product['ml_score']],
                theta=theta_cats, fill="toself", name="This Asset",
                line=dict(color=ACCENT_COLOR, width=2), fillcolor="rgba(14,165,233,0.1)"
            ))
            apply_theme(fig_p, "Benchmarking: Asset vs Group Average", height=320)
            st.plotly_chart(fig_p, use_container_width=True)

        with m_right:
            st.markdown('<div class="section-heading"><i class="bi bi-lightning-charge"></i>&nbsp; AI Synthesis Report</div>', unsafe_allow_html=True)
            
            report_html = f"""
<div style="background:linear-gradient(135deg, rgba(14,165,233,0.05), rgba(99,102,241,0.05)); border:1px solid rgba(14,165,233,0.15); border-radius:16px; padding:1.8rem; line-height:1.75;">
<div style="font-weight:700; color:var(--accent); font-size:0.9rem; margin-bottom:1rem; display:flex; align-items:center; gap:8px;">
<i class="bi bi-patch-check"></i> ML Intelligence Verdict
</div>
<div style="font-size:0.9rem; color:var(--text); font-style:italic; margin-bottom:1.5rem;">
"{product['short_description'] or 'Automatic categorization and assessment complete. No custom descriptive report generated for this asset yet.'}"
</div>
<hr style="border-top:1px solid rgba(255,255,255,0.05); margin:1.5rem 0;">
<div style="font-weight:700; color:var(--indigo); font-size:0.9rem; margin-bottom:0.8rem; display:flex; align-items:center; gap:8px;">
<i class="bi bi-target"></i> Strategic Persona Alignment
</div>
"""
            if product['persona_json']:
                try:
                    per = json.loads(product['persona_json'])
                    report_html += f"""
<div style="font-size:0.85rem; color:var(--text);">
<b style="color:var(--accent);">Audience:</b> {per.get('nom_persona','Target User')}<br>
<b style="color:var(--accent);">Lifestyle:</b> {per.get('style_vie','N/A')}<br>
<b style="color:var(--accent);">Key Traits:</b> {per.get('traits_personnalite','N/A')}<br>
<b style="color:var(--accent);">Opportunity:</b> Ideal for {per.get('occasion_port','any occasion')} based on material durability.
</div>
"""
                except: 
                    report_html += '<div style="font-size:0.8rem; color:var(--muted);">JSON structure error in persona data.</div>'
            else:
                report_html += '<div style="font-size:0.8rem; color:var(--muted);">No deep-learning persona profile discovered for this SKU.</div>'
            
            report_html += "</div>"
            st.markdown(report_html, unsafe_allow_html=True)

            st.markdown('<div class="section-heading" style="margin-top:2rem;"><i class="bi bi-link-45deg"></i>&nbsp; External Connectivity</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <a href="{product['product_url']}" target="_blank" style="text-decoration:none;">
                <div style="background:var(--accent); color:white; border-radius:12px; padding:12px; text-align:center; font-weight:700; font-size:0.9rem;">
                   <i class="bi bi-box-arrow-up-right"></i> View Original Asset Listing
                </div>
            </a>
            """, unsafe_allow_html=True)

    else:
        st.markdown('<div class="section-heading"><i class="bi bi-collection"></i>&nbsp; Asset Catalog Gallery</div>', unsafe_allow_html=True)

        s1, s2, s3 = st.columns([3, 1, 1])
        with s1:
            search_query = st.text_input("Search catalog...", placeholder="Name, brand, cluster...", label_visibility="collapsed")
        with s2:
            csv = fdf.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export CSV", data=csv, file_name="catalog.csv", use_container_width=True)
        with s3:
            st.caption(f"Index: {len(fdf):,} Items")

        if search_query:
            fdf = fdf[fdf['product_name'].str.contains(search_query, case=False, na=False) | 
                      fdf['brand'].str.contains(search_query, case=False, na=False)]

        items_per_row = 4
        rows = [fdf.iloc[i:i+items_per_row] for i in range(0, min(80, len(fdf)), items_per_row)]
        
        for row in rows:
            cols = st.columns(items_per_row)
            for i, (_, item) in enumerate(row.iterrows()):
                with cols[i]:
                    st.markdown(f"""
                    <div class="prod-card">
                        <img src="{item['image_url_main']}" style="width:100%; height:140px; object-fit:cover; border-radius:10px; margin-bottom:0.8rem;">
                        <div style="font-size:0.65rem; color:var(--accent); font-weight:700; margin-bottom:0.3rem;">{item['brand']}</div>
                        <div class="prod-name" style="min-height:2.6rem; font-size:0.85rem;">{item['product_name'][:45]}...</div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.5rem;">
                            <span style="font-weight:800; font-size:1rem;">${item['current_price']:.0f}</span>
                            <span class="prod-badge">{item['ml_score']:.0f} AI</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"🔬 Deep Dive", key=f"btn_{item['product_id']}", use_container_width=True):
                        st.session_state.detail_view_id = item['product_id']
                        st.rerun()

elif selected_page == "AI Insight Hub":
    st.markdown('<div class="section-heading"><i class="bi bi-robot"></i>&nbsp; Strategic AI Intelligence</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#131918;border:1px solid rgba(61,255,192,0.1);border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:1.2rem;font-size:0.82rem;color:#5e7d75;line-height:1.7;">
    Generate a strategic intelligence report powered by Groq LLM. The report analyses current catalog data,
    market positioning, top brands, score distribution and pricing strategy.
    </div>
    """, unsafe_allow_html=True)

    if st.button("✨ Generate AI Market Report"):
        from groq import Groq
        groq_keys = [k.strip() for k in os.getenv("GROQ_KEYS", "").split(",") if k.strip()]
        gemini_keys = [k.strip() for k in os.getenv("GEMINI_KEYS", "").split(",") if k.strip()]
        
        bstats_local = df.groupby("brand").agg(Avg_Score=("ml_score","mean")).round(1)
        top_brand_local = bstats_local['Avg_Score'].idxmax()
        summary_raw = (
            f"Catalog: {len(df)} products, {df['brand'].nunique()} brands. "
            f"Avg AI Score: {df['ml_score'].mean():.1f}/100. "
            f"Median Price: ${df['current_price'].median():.0f}. "
            f"Top Brand by Score: {top_brand_local}. "
            f"Masterpiece tier (90+): {len(df[df['ml_score']>=90])} products. "
            f"In Stock: {in_stock_count}/{len(df)} SKUs."
        )

        report_content = None
        
        if groq_keys:
        # 1. Try Groq first
            with st.spinner("Analyzing with Groq (Primary)..."):
                for key in groq_keys:
                    try:
                        client = Groq(api_key=key)
                        resp = client.chat.completions.create(
                            messages=[
                                {"role":"system","content":"You are a luxury footwear market analyst. Provide concise, insightful strategic analysis in English. Use bullet points and clear sections."},
                                {"role":"user","content":f"Analyze this e-commerce catalog data and provide strategic recommendations:\n\n{summary_raw}"}
                            ],
                            model="llama-3.1-8b-instant"
                        )
                        report_content = resp.choices[0].message.content
                        break
                    except: continue

        if not report_content and HAS_GEMINI and gemini_keys:
            with st.spinner("Groq unavailable. Failing over to Gemini (Backup)..."):
                for key in gemini_keys:
                    try:
                        genai.configure(api_key=key)
                        model = genai.GenerativeModel("gemini-2.0-flash")
                        response = model.generate_content(
                            f"System: You are a luxury footwear market analyst. Provide concise, insightful strategic analysis in English. Use bullet points and clear sections.\n\nUser: Analyze this e-commerce catalog data:\n{summary_raw}"
                        )
                        report_content = response.text
                        break
                    except: continue

        if report_content:
            st.markdown(f"""
            <div style="background:#131918;border:1px solid rgba(14,165,233,0.15);border-radius:12px;padding:1.8rem;line-height:1.75;font-size:0.85rem;color:#ddeee9;box-shadow:0 8px 32px rgba(0,0,0,0.4);">
            <div style="font-family:'Inter',sans-serif;font-weight:700;color:var(--accent);margin-bottom:1.5rem;display:flex;align-items:center;gap:10px;">
                <i class="bi bi-journal-text"></i> Market Intelligence Report Generated
            </div>
            {report_content.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Failed to generate report. All AI providers (Groq & Gemini) are unresponsive or keys have expired.")

elif selected_page == "Responsible AI":
    st.markdown('<div class="section-heading"><i class="bi bi-shield-check"></i>&nbsp; Responsible AI Architecture</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div style="background:#131918;border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:1.4rem;">
            <div style="font-family:'Inter',sans-serif;font-size:0.9rem;font-weight:700;color:#0ea5e9;margin-bottom:1rem;">
                <i class="bi bi-diagram-3"></i>&nbsp; MCP Governance Principles
            </div>
            <div style="font-size:0.8rem;color:#94a3b8;line-height:2;">
                ✅ &nbsp;<b style="color:#f8fafc">Modular Autonomy</b> — Logic/Compute separation<br>
                ✅ &nbsp;<b style="color:#f8fafc">Traceability</b> — Blockchain-like audit trails<br>
                ✅ &nbsp;<b style="color:#f8fafc">Safety Isolation</b> — Zero raw exposure<br>
                ✅ &nbsp;<b style="color:#f8fafc">Quota Enforcement</b> — Usage governance<br>
                ✅ &nbsp;<b style="color:#f8fafc">Alignment</b> — Policy-driven decisions<br>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        try:
            from step6_responsible_ai_mcp import ShoeMCPServer
            server = ShoeMCPServer()
            tools = server.list_tools()
            st.json(tools)
            if st.button("▶ Simulate Responsible Tool Call"):
                result = server.call_tool("get_top_shoes", {"limit": 2})
                st.success("✅ Tool Executed Successfully")
                st.json(result)
        except ImportError:
            st.markdown("""
            <div style="background:#131918;border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:1.4rem;font-size:0.78rem;color:#5e7d75;">
            <b style="color:#ddeee9">MCP Server module not found.</b><br><br>
            To enable this tab, ensure <code>step6_responsible_ai_mcp.py</code> is in the same directory
            and exposes a <code>ShoeMCPServer</code> class with <code>list_tools()</code>
            and <code>call_tool(name, args)</code> methods.
            </div>
            """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;padding:2.5rem 0 1rem;font-size:0.6rem;
color:#2a3532;text-transform:uppercase;letter-spacing:0.2em;">
Smart Shoe — Business Intelligence Platform &nbsp;·&nbsp; AI-Powered Catalog Analytics
</div>
""", unsafe_allow_html=True)
