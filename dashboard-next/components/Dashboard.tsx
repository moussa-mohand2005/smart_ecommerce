"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity, BarChart3, Bot, Boxes, BrainCircuit, ChevronLeft, ChevronRight,
  CircleDollarSign, Database, ExternalLink, Filter, Gauge, Layers3, LoaderCircle,
  PackageCheck, RefreshCw, Search, ShieldCheck, Sparkles, Star, Store, Tags, X,
} from "lucide-react";
import {
  Bar, BarChart, CartesianGrid, Cell, ComposedChart, Legend, Line, Pie, PieChart,
  ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis,
} from "recharts";
import type { DashboardData, Product } from "@/lib/types";

const tabs = [
  ["picks", "Top Picks", Star], ["market", "Market Analysis", BarChart3],
  ["clusters", "Style Clusters", Boxes], ["personas", "Personas", Tags],
  ["brands", "Brand Intelligence", Store], ["data", "Data Explorer", Database],
  ["insights", "AI Insight Hub", BrainCircuit], ["mcp", "Agent Reflection", ShieldCheck],
] as const;

const palette = ["#d6b45d", "#66c7b2", "#e58c72", "#8ca9ff", "#b18cff", "#4b8f80", "#f0cf7a", "#cf6f83"];

type Filters = { brands: string[]; minPrice: number; maxPrice: number; minScore: number; search: string; page: number };
const initialFilters: Filters = { brands: [], minPrice: 0, maxPrice: 1_000_000, minScore: 0, search: "", page: 1 };

function money(value: number, currency = "USD") {
  try { return new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: 0 }).format(value); }
  catch { return `$${Math.round(value).toLocaleString()}`; }
}

function compact(value: number) {
  return new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

function statusLabel(value: string) {
  return ["in_stock", "instock"].includes(value.toLowerCase()) ? "In stock" : value.replaceAll("_", " ");
}

function Panel({ title, eyebrow, children, className = "" }: { title: string; eyebrow?: string; children: React.ReactNode; className?: string }) {
  return <section className={`panel ${className}`}><div className="panel-heading"><div>{eyebrow && <span>{eyebrow}</span>}<h3>{title}</h3></div></div>{children}</section>;
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: Array<{ name: string; value: number; color?: string; payload?: Record<string, unknown> }> }) {
  if (!active || !payload?.length) return null;
  const label = String(payload[0]?.payload?.name ?? payload[0]?.payload?.band ?? payload[0]?.payload?.cluster ?? "");
  return <div className="chart-tooltip">{label && <strong>{label}</strong>}{payload.map((item, index) => <span key={`${item.name}-${index}`}><i style={{ background: item.color }} />{item.name}: {Number(item.value).toLocaleString(undefined, { maximumFractionDigits: 1 })}</span>)}</div>;
}

function Empty({ message }: { message: string }) {
  return <div className="empty"><Activity size={24} /><p>{message}</p></div>;
}

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number][0]>("picks");
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const initializedPrice = useRef(false);

  const fetchData = useCallback(async (signal?: AbortSignal) => {
    setLoading(true); setError("");
    const query = new URLSearchParams({ minPrice: String(filters.minPrice), maxPrice: String(filters.maxPrice), minScore: String(filters.minScore), search: filters.search, page: String(filters.page), pageSize: "25" });
    filters.brands.forEach((brand) => query.append("brand", brand));
    try {
      const response = await fetch(`/api/dashboard?${query}`, { cache: "no-store", signal });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error ?? "Unable to load data");
      setData(payload);
      if (!initializedPrice.current && payload.filters.priceMax > 0) {
        initializedPrice.current = true;
        setFilters((current) => ({ ...current, maxPrice: payload.filters.priceMax }));
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") setError((err as Error).message);
    } finally { if (!signal?.aborted) setLoading(false); }
  }, [filters]);

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => fetchData(controller.signal), 250);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [fetchData]);

  const updateFilter = <K extends keyof Filters>(key: K, value: Filters[K]) => setFilters((current) => ({ ...current, [key]: value, page: key === "page" ? Number(value) : 1 }));
  const clearFilters = () => { initializedPrice.current = false; setFilters(initialFilters); };
  const hasFilters = filters.brands.length > 0 || filters.minPrice > 0 || filters.minScore > 0 || Boolean(filters.search);

  return (
    <main>
      <div className="ambient ambient-one" /><div className="ambient ambient-two" />
      <header className="topbar">
        <div className="brand-lockup"><div className="logo-mark"><Layers3 size={19} /></div><div><b>SMART SHOE</b><span>INTELLIGENCE SYSTEM</span></div></div>
        <div className="topbar-actions"><span className="live"><i /> LIVE DATA</span><button className="icon-button" onClick={() => fetchData()} aria-label="Refresh"><RefreshCw size={17} className={loading ? "spin" : ""} /></button></div>
      </header>

      <div className="app-shell">
        <aside className={`filters ${filtersOpen ? "open" : ""}`}>
          <div className="filters-title"><div className="filter-title-copy"><span>CATALOG CONTROL</span><strong>Refine your view</strong></div><button onClick={() => setFiltersOpen(false)} aria-label="Close filters"><X size={18} /></button></div>
          <div className="filter-overview"><div><span>Live selection</span><strong>{data ? data.kpis.total.toLocaleString() : "—"}</strong><small>matching products</small></div><div className="filter-orbit"><Filter size={17}/>{hasFilters && <i/>}</div></div>
          <label className="search-box"><Search size={16} /><input value={filters.search} onChange={(e) => updateFilter("search", e.target.value)} placeholder="Product, brand, material…" />{filters.search && <button onClick={() => updateFilter("search", "")} aria-label="Clear search"><X size={13}/></button>}</label>
          <div className="filter-group"><div className="filter-section-title"><Gauge size={14}/><span>Performance</span><small>01</small></div><div className="filter-label"><span>Minimum smart score</span><b>{filters.minScore}</b></div><input type="range" min="0" max="100" value={filters.minScore} onChange={(e) => updateFilter("minScore", Number(e.target.value))} /><div className="range-scale"><span>0</span><span>50</span><span>100</span></div></div>
          <div className="filter-group"><div className="filter-section-title"><CircleDollarSign size={14}/><span>Price window</span><small>02</small></div><div className="filter-label"><span>Minimum</span><b>{money(filters.minPrice)}</b></div><input type="range" min="0" max={Math.max(data?.filters.priceMax ?? 1000, 1)} step="10" value={filters.minPrice} onChange={(e) => updateFilter("minPrice", Math.min(Number(e.target.value), filters.maxPrice))} /><div className="filter-label price-max-label"><span>Maximum</span><b>{money(filters.maxPrice)}</b></div><input type="range" min="0" max={Math.max(data?.filters.priceMax ?? 1000, 1)} step="10" value={Math.min(filters.maxPrice, data?.filters.priceMax ?? filters.maxPrice)} onChange={(e) => updateFilter("maxPrice", Math.max(Number(e.target.value), filters.minPrice))} /></div>
          <div className="filter-group brand-filter"><div className="filter-section-title"><Store size={14}/><span>Brands</span><small>03</small></div><div className="filter-label"><span>Selected labels</span><b>{filters.brands.length || "All"}</b></div><div className="brand-list">{data?.filters.brands.map((brand) => <label key={brand}><input type="checkbox" checked={filters.brands.includes(brand)} onChange={() => updateFilter("brands", filters.brands.includes(brand) ? filters.brands.filter((item) => item !== brand) : [...filters.brands, brand])} /><i/><span>{brand}</span></label>)}</div></div>
          <button className="clear-button" disabled={!hasFilters} onClick={clearFilters}><RefreshCw size={13}/> Reset filters</button>
          <div className="data-note"><div className="connection-icon"><Database size={14}/><i/></div><span>MySQL connection<b>{data ? "Operational · live data" : "Synchronizing…"}</b></span></div>
        </aside>

        <div className="content">
          <button className="mobile-filter standalone-filter" onClick={() => setFiltersOpen(true)}><Filter size={16} /> Filters {hasFilters && <i />}</button>

          {error ? <div className="error-state"><Database size={28}/><div><b>Dashboard unavailable</b><p>{error}</p></div><button onClick={() => fetchData()}>Try again</button></div> : !data ? <div className="page-loader"><LoaderCircle className="spin"/><span>Curating intelligence…</span></div> : <>
            <Kpis data={data} />
            <nav className="tabs" aria-label="Dashboard sections">{tabs.map(([id, label, Icon]) => <button key={id} className={activeTab === id ? "active" : ""} onClick={() => setActiveTab(id)}><Icon size={15}/><span>{label}</span></button>)}</nav>
            <div className={loading ? "section-loading" : ""}>
              {activeTab === "picks" && <TopPicks products={data.topPicks}/>}
              {activeTab === "market" && <Market data={data}/>}
              {activeTab === "clusters" && <Clusters data={data}/>}
              {activeTab === "personas" && <Personas data={data}/>}
              {activeTab === "brands" && <Brands data={data}/>}
              {activeTab === "data" && <DataExplorer data={data} filters={filters} setPage={(page) => updateFilter("page", page)}/>}
              {activeTab === "insights" && <Insights data={data}/>}
              {activeTab === "mcp" && <Mcp data={data}/>}
            </div>
          </>}
          <footer>SMART SHOE <i/> BUSINESS INTELLIGENCE PLATFORM <span>© 2026</span></footer>
        </div>
      </div>
    </main>
  );
}

function Kpis({ data }: { data: DashboardData }) {
  const items = [
    ["Unique items", data.kpis.total.toLocaleString(), Gauge, "Filtered catalog"],
    ["Average score", data.kpis.avgScore.toFixed(1), Sparkles, "AI smart score"],
    ["Active brands", data.kpis.brands.toLocaleString(), Store, "In this view"],
    ["Luxury tier", data.kpis.luxury.toLocaleString(), Star, "Score 90+"],
    ["Median price", money(data.kpis.medianPrice), CircleDollarSign, "Catalog midpoint"],
    ["In stock", data.kpis.inStock.toLocaleString(), PackageCheck, `${data.kpis.total ? Math.round(data.kpis.inStock / data.kpis.total * 100) : 0}% availability`],
  ] as const;
  return <div className="kpi-grid">{items.map(([label, value, Icon, note]) => <article className="kpi" key={label}><div className="kpi-icon"><Icon size={17}/></div><span>{label}</span><strong>{value}</strong><small>{note}</small></article>)}</div>;
}

function TopPicks({ products }: { products: Product[] }) {
  if (!products.length) return <Empty message="No products match the current filters."/>;
  return <div><div className="section-intro"><div><span>CURATED BY PERFORMANCE</span><h2>Top-scoring products</h2></div><p>The strongest catalog opportunities, ranked by the current ML score.</p></div><div className="product-grid">{products.map((product, index) => <article className="product-card" key={product.product_id}><div className="product-image">{product.image_url_main ? <img src={product.image_url_main} alt="" loading="lazy"/> : <div className="image-fallback"><Star/></div>}<span className="rank">#{String(index + 1).padStart(2, "0")}</span><span className={`stock ${statusLabel(product.stock_status) === "In stock" ? "available" : ""}`}>{statusLabel(product.stock_status)}</span></div><div className="product-body"><div className="brand-name">{product.brand}</div><h3>{product.product_name}</h3><div className="score-row"><div><i style={{ width: `${Math.min(100, product.ml_score)}%` }}/></div><b>{product.ml_score.toFixed(1)}</b></div><div className="product-meta"><strong>{money(product.current_price, product.currency)}</strong><span><Star size={13} fill="currentColor"/> {product.rating_avg.toFixed(1)} · {compact(product.reviews_count)} reviews</span></div>{product.product_url && <a href={product.product_url} target="_blank" rel="noreferrer">View product <ExternalLink size={13}/></a>}</div></article>)}</div></div>;
}

function Market({ data }: { data: DashboardData }) {
  return <><div className="section-intro"><div><span>COMMERCIAL LANDSCAPE</span><h2>Market analysis</h2></div><p>Price positioning, demand signals and score distribution across the filtered catalog.</p></div><div className="chart-grid"><Panel eyebrow="POSITIONING" title="Price vs. smart score"><div className="chart"><ResponsiveContainer><ScatterChart margin={{top:15,right:15,bottom:15,left:0}}><CartesianGrid stroke="#20312c" strokeDasharray="3 6"/><XAxis type="number" dataKey="price" name="Price" stroke="#658078" fontSize={11}/><YAxis type="number" dataKey="score" name="Score" domain={[0,100]} stroke="#658078" fontSize={11}/><ZAxis type="number" dataKey="reviews" range={[35,260]}/><Tooltip content={<ChartTooltip/>}/><Scatter data={data.marketScatter} fill="#d6b45d">{data.marketScatter.map((item, i) => <Cell key={i} fill={palette[item.cluster % palette.length]} fillOpacity={0.72}/>)}</Scatter></ScatterChart></ResponsiveContainer></div></Panel><Panel eyebrow="PRICE ARCHITECTURE" title="Products by price band"><div className="chart"><ResponsiveContainer><ComposedChart data={data.priceBands} margin={{top:15,right:5,bottom:15,left:0}}><CartesianGrid stroke="#20312c" strokeDasharray="3 6" vertical={false}/><XAxis dataKey="band" stroke="#658078" fontSize={10}/><YAxis yAxisId="left" stroke="#658078" fontSize={11}/><YAxis yAxisId="right" orientation="right" domain={[0,100]} stroke="#d6b45d" fontSize={11}/><Tooltip content={<ChartTooltip/>}/><Bar yAxisId="left" dataKey="count" name="Products" fill="#285f53" radius={[5,5,0,0]}/><Line yAxisId="right" type="monotone" dataKey="avgScore" name="Avg score" stroke="#e7c768" strokeWidth={2.5} dot={{fill:"#e7c768",r:3}}/></ComposedChart></ResponsiveContainer></div></Panel></div></>;
}

function Clusters({ data }: { data: DashboardData }) {
  return <><div className="section-intro"><div><span>UNSUPERVISED LEARNING</span><h2>Style clusters</h2></div><p>Catalog composition and the two-dimensional PCA map generated from product attributes.</p></div><div className="cluster-layout"><Panel eyebrow="COMPOSITION" title="Products per cluster"><div className="chart"><ResponsiveContainer><PieChart><Pie data={data.clusters} dataKey="count" nameKey="cluster" innerRadius="58%" outerRadius="82%" paddingAngle={3}>{data.clusters.map((_, i) => <Cell key={i} fill={palette[i % palette.length]}/>)}</Pie><Tooltip content={<ChartTooltip/>}/><Legend iconType="circle" wrapperStyle={{fontSize:11,color:"#8ca39d"}}/></PieChart></ResponsiveContainer></div></Panel><Panel eyebrow="PRODUCT DNA" title={data.styleMap.length ? "AI-generated style map" : "Style score landscape"}><div className="chart"><ResponsiveContainer>{data.styleMap.length ? <ScatterChart margin={{top:15,right:15,bottom:15,left:0}}><CartesianGrid stroke="#20312c" strokeDasharray="3 6"/><XAxis type="number" dataKey="x" name="PCA X" stroke="#658078" fontSize={11}/><YAxis type="number" dataKey="y" name="PCA Y" stroke="#658078" fontSize={11}/><ZAxis type="number" dataKey="score" range={[22,100]}/><Tooltip content={<ChartTooltip/>}/><Scatter data={data.styleMap}>{data.styleMap.map((item, i) => <Cell key={i} fill={palette[item.cluster % palette.length]} fillOpacity={0.68}/>)}</Scatter></ScatterChart> : <BarChart data={data.clusters}><CartesianGrid stroke="#20312c" strokeDasharray="3 6" vertical={false}/><XAxis dataKey="cluster" stroke="#658078" fontSize={10}/><YAxis domain={[0,100]} stroke="#658078" fontSize={10}/><Tooltip content={<ChartTooltip/>}/><Bar dataKey="avgScore" name="Avg score" fill="#66c7b2" radius={[5,5,0,0]}/></BarChart>}</ResponsiveContainer></div></Panel></div></>;
}

function Personas({ data }: { data: DashboardData }) {
  return <><div className="section-intro"><div><span>LLM-ENRICHED PROFILES</span><h2>Customer personas</h2></div><p>Ideal audiences inferred from product identity, style and brand positioning.</p></div>{data.personas.length ? <div className="persona-grid">{data.personas.map((persona, i) => <article className="persona" key={persona.productId}><div className="persona-number">0{i+1}</div><span>{persona.brand}</span><h3>{persona.name}</h3><p className="persona-product">{persona.productName}</p><div className="persona-facts"><div><small>Audience</small><b>{persona.age}</b></div><div><small>Lifestyle</small><b>{persona.lifestyle}</b></div></div><blockquote>“{persona.traits || "No personality traits available."}”</blockquote>{persona.occasion && <footer>Best occasion · {persona.occasion}</footer>}</article>)}</div> : <Empty message="No valid persona profiles are available for this selection."/>}</>;
}

function Brands({ data }: { data: DashboardData }) {
  const ranking = [...data.brandStats].sort((a,b) => a.avgScore-b.avgScore).slice(-12);
  return <><div className="section-intro"><div><span>COMPETITIVE INTELLIGENCE</span><h2>Brand intelligence</h2></div><p>Compare quality, pricing, assortment size and customer engagement by brand.</p></div><div className="chart-grid"><Panel eyebrow="QUALITY" title="Brand score ranking"><div className="chart tall"><ResponsiveContainer><BarChart data={ranking} layout="vertical" margin={{left:15,right:25}}><CartesianGrid stroke="#20312c" strokeDasharray="3 6" horizontal={false}/><XAxis type="number" domain={[0,100]} stroke="#658078" fontSize={11}/><YAxis dataKey="brand" type="category" width={100} stroke="#8ca39d" fontSize={10}/><Tooltip content={<ChartTooltip/>}/><Bar dataKey="avgScore" name="Avg score" fill="#d6b45d" radius={[0,5,5,0]}/></BarChart></ResponsiveContainer></div></Panel><Panel eyebrow="POSITIONING" title="Price vs. brand score"><div className="chart tall"><ResponsiveContainer><ScatterChart margin={{top:15,right:15,bottom:15,left:0}}><CartesianGrid stroke="#20312c" strokeDasharray="3 6"/><XAxis type="number" dataKey="avgPrice" name="Avg price" stroke="#658078" fontSize={11}/><YAxis type="number" dataKey="avgScore" name="Avg score" domain={[0,100]} stroke="#658078" fontSize={11}/><ZAxis type="number" dataKey="products" range={[80,500]}/><Tooltip content={<ChartTooltip/>}/><Scatter data={data.brandStats} fill="#66c7b2" fillOpacity={0.78}/></ScatterChart></ResponsiveContainer></div></Panel></div><Panel eyebrow="ATTRIBUTE AFFINITY" title="Footwear correlations" className="correlation-panel">{data.correlations.length ? <div className="correlations">{data.correlations.map((rule,i) => <div key={i}><span>{rule.antecedents}</span><ChevronRight size={14}/><span>{rule.consequents}</span><b>Lift {rule.lift.toFixed(2)}</b></div>)}</div> : <Empty message="No association-rule export found. Run the ML analytics stage to generate footwear_correlations.csv."/>}</Panel></>;
}

function DataExplorer({ data, filters, setPage }: { data: DashboardData; filters: Filters; setPage: (page:number)=>void }) {
  return <><div className="section-intro"><div><span>CATALOG RECORDS</span><h2>Data explorer</h2></div><p>Inspect enriched fields, model outputs and source links with server-side pagination.</p></div><Panel title={`${data.pagination.total.toLocaleString()} matching products`} eyebrow={filters.search ? `SEARCH · ${filters.search}` : "LIVE DATABASE"}><div className="table-wrap"><table><thead><tr><th>Product</th><th>Brand</th><th>Price</th><th>Material</th><th>Gender</th><th>Stock</th><th>Smart score</th><th>Cluster</th><th/></tr></thead><tbody>{data.products.map((product) => <tr key={product.product_id}><td><div className="table-product">{product.image_url_main ? <img src={product.image_url_main} alt="" loading="lazy"/> : <div/>}<span>{product.product_name}<small>#{product.product_id}</small></span></div></td><td>{product.brand}</td><td>{money(product.current_price, product.currency)}</td><td>{product.material || "—"}</td><td>{product.gender || "—"}</td><td><span className={`status-pill ${statusLabel(product.stock_status)==="In stock"?"good":""}`}>{statusLabel(product.stock_status)}</span></td><td><div className="table-score"><i><b style={{width:`${Math.min(100,product.ml_score)}%`}}/></i><span>{product.ml_score.toFixed(1)}</span></div></td><td>#{product.cluster_id}</td><td>{product.product_url && <a href={product.product_url} target="_blank" rel="noreferrer" aria-label="Open product"><ExternalLink size={15}/></a>}</td></tr>)}</tbody></table></div><div className="pagination"><span>Page {data.pagination.page} of {data.pagination.pages}</span><div><button disabled={data.pagination.page<=1} onClick={()=>setPage(data.pagination.page-1)}><ChevronLeft size={16}/></button><button disabled={data.pagination.page>=data.pagination.pages} onClick={()=>setPage(data.pagination.page+1)}><ChevronRight size={16}/></button></div></div></Panel></>;
}

function Insights({ data }: { data: DashboardData }) {
  const [insight,setInsight]=useState(""); const [error,setError]=useState(""); const [loading,setLoading]=useState(false);
  const generate=async()=>{setLoading(true);setError("");try{const top=data.brandStats[0];const response=await fetch("/api/insights",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({products:data.kpis.total,averageScore:data.kpis.avgScore,topBrand:top?.brand,averagePrice:top?.avgPrice,inStock:data.kpis.inStock})});const result=await response.json();if(!response.ok)throw new Error(result.error);setInsight(result.insight);}catch(err){setError((err as Error).message)}finally{setLoading(false)}};
  return <><div className="section-intro"><div><span>GENERATIVE INTELLIGENCE</span><h2>AI insight hub</h2></div><p>Turn the current filtered view into a concise, actionable executive market brief.</p></div><div className="insight-layout"><Panel eyebrow="CURRENT SIGNAL" title="Analysis context"><div className="context-list"><div><span>Products in scope</span><b>{data.kpis.total.toLocaleString()}</b></div><div><span>Average score</span><b>{data.kpis.avgScore.toFixed(1)}</b></div><div><span>Leading brand</span><b>{data.brandStats[0]?.brand ?? "N/A"}</b></div><div><span>Availability</span><b>{data.kpis.total ? Math.round(data.kpis.inStock/data.kpis.total*100) : 0}%</b></div></div><button className="primary-button" onClick={generate} disabled={loading}>{loading?<LoaderCircle className="spin" size={17}/>:<Sparkles size={17}/>} {loading?"Analyzing catalog…":"Generate strategic report"}</button></Panel><Panel eyebrow="EXECUTIVE BRIEF" title="Strategic market intelligence" className="report-panel">{error?<div className="inline-error">{error}</div>:insight?<div className="report">{insight}</div>:<div className="report-placeholder"><Bot size={36}/><p>Your AI-generated analysis will appear here.</p><span>It uses only aggregate catalog signals and keeps the API key server-side.</span></div>}</Panel></div></>;
}

function Mcp({ data }: { data: DashboardData }) {
  const [tool,setTool]=useState("get_top_shoes"); const [value,setValue]=useState("5"); const [result,setResult]=useState<unknown>(null); const [loading,setLoading]=useState(false);
  const execute=async()=>{setLoading(true);try{const params=tool==="get_top_shoes"?{limit:value}:{cluster_id:value};const response=await fetch("/api/mcp",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:tool,params})});setResult(await response.json())}finally{setLoading(false)}};
  return <><div className="section-intro"><div><span>RESPONSIBLE AI ARCHITECTURE</span><h2>Agent reflection & tools</h2></div><p>A constrained server-side tool layer with validation, parameterized queries and execution receipts.</p></div><div className="mcp-grid"><Panel eyebrow="GUARDRAILS" title="Controlled agent access"><div className="principles"><div><ShieldCheck/><span><b>Validated inputs</b><small>Limits and identifiers are checked before execution.</small></span></div><div><Layers3/><span><b>Decoupled tools</b><small>The browser never receives database credentials.</small></span></div><div><Activity/><span><b>Execution receipt</b><small>Every response includes validation and timestamp metadata.</small></span></div></div></Panel><Panel eyebrow="TOOL CONSOLE" title="Simulate a responsible call"><div className="tool-form"><label>Available tool<select value={tool} onChange={(e)=>{setTool(e.target.value);setValue(e.target.value==="get_top_shoes"?"5":String(data.clusters[0]?.cluster.replace("Cluster ","")??0))}}><option value="get_top_shoes">get_top_shoes</option><option value="analyze_cluster">analyze_cluster</option></select></label><label>{tool==="get_top_shoes"?"Result limit":"Cluster ID"}<input type="number" min="0" max="20" value={value} onChange={(e)=>setValue(e.target.value)}/></label><button className="primary-button" onClick={execute} disabled={loading}>{loading?<LoaderCircle className="spin" size={17}/>:<Bot size={17}/>} Execute validated tool</button></div>{result!==null&&<pre className="json-result">{JSON.stringify(result,null,2)}</pre>}</Panel></div></>;
}
