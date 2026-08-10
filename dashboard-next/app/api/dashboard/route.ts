import { NextRequest, NextResponse } from "next/server";
import type { RowDataPacket } from "mysql2";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { pool } from "@/lib/db";
import type { DashboardData, Persona, Product } from "@/lib/types";

export const dynamic = "force-dynamic";

const productFields = `
  product_id, COALESCE(product_name, 'Untitled') product_name,
  COALESCE(brand, 'Unknown') brand, product_url, image_url_main,
  COALESCE(current_price, 0) current_price, COALESCE(currency, 'USD') currency,
  COALESCE(rating_avg, 0) rating_avg, COALESCE(reviews_count, 0) reviews_count,
  COALESCE(stock_status, 'unknown') stock_status, material, sole_type, closure, gender,
  persona_json, COALESCE(ml_score, 0) ml_score,
  COALESCE(predicted_success, 0) predicted_success,
  COALESCE(cluster_id, 0) cluster_id, pca_x, pca_y`;

function getFilters(request: NextRequest) {
  const sp = request.nextUrl.searchParams;
  const brands = sp.getAll("brand").filter(Boolean).slice(0, 30);
  const minPrice = Math.max(0, Number(sp.get("minPrice") ?? 0) || 0);
  const maxPrice = Math.max(minPrice, Number(sp.get("maxPrice") ?? 1_000_000) || 1_000_000);
  const minScore = Math.min(100, Math.max(0, Number(sp.get("minScore") ?? 0) || 0));
  const search = (sp.get("search") ?? "").trim().slice(0, 100);
  const page = Math.max(1, Number.parseInt(sp.get("page") ?? "1", 10) || 1);
  const pageSize = Math.min(100, Math.max(10, Number.parseInt(sp.get("pageSize") ?? "25", 10) || 25));
  return { brands, minPrice, maxPrice, minScore, search, page, pageSize };
}

function whereClause(filters: ReturnType<typeof getFilters>) {
  const clauses = ["COALESCE(current_price, 0) BETWEEN ? AND ?", "COALESCE(ml_score, 0) >= ?"];
  const params: Array<string | number> = [filters.minPrice, filters.maxPrice, filters.minScore];
  if (filters.brands.length) {
    clauses.push(`brand IN (${filters.brands.map(() => "?").join(",")})`);
    params.push(...filters.brands);
  }
  if (filters.search) {
    clauses.push("(product_name LIKE ? OR brand LIKE ? OR material LIKE ?)");
    const term = `%${filters.search}%`;
    params.push(term, term, term);
  }
  return { sql: `WHERE ${clauses.join(" AND ")}`, params };
}

function parsePersona(row: Product): Persona | null {
  if (!row.persona_json) return null;
  try {
    const value = typeof row.persona_json === "string" ? JSON.parse(row.persona_json) : row.persona_json;
    return {
      productId: row.product_id,
      productName: row.product_name,
      brand: row.brand,
      name: value.nom_persona ?? value.name ?? "Undefined persona",
      age: value.age_cible ?? value.age ?? "N/A",
      lifestyle: value.style_vie ?? value.lifestyle ?? "N/A",
      traits: value.traits_personnalite ?? value.traits ?? "",
      occasion: value.occasion_port ?? value.occasion ?? "",
    };
  } catch {
    return null;
  }
}

async function readCorrelations() {
  try {
    const csv = await readFile(path.resolve(process.cwd(), "..", "footwear_correlations.csv"), "utf8");
    return csv.split(/\r?\n/).slice(1).filter(Boolean).slice(0, 10).map((line) => {
      const parts = line.match(/("[^"]*"|[^,])+/g)?.map((part) => part.replace(/^"|"$/g, "")) ?? [];
      return { antecedents: parts[0] ?? "", consequents: parts[1] ?? "", lift: Number(parts[6] ?? parts.at(-1) ?? 0) };
    });
  } catch {
    return [];
  }
}

export async function GET(request: NextRequest) {
  try {
    const filters = getFilters(request);
    const where = whereClause(filters);
    const offset = (filters.page - 1) * filters.pageSize;

    const [metaResult, maxPriceResult, countResult, kpiResult, pricesResult, topResult, scatterResult, bandResult, clusterResult, styleResult, personaResult, brandResult, productsResult, correlations] = await Promise.all([
      pool.query<RowDataPacket[]>("SELECT DISTINCT COALESCE(brand, 'Unknown') brand FROM products ORDER BY brand"),
      pool.query<RowDataPacket[]>("SELECT COALESCE(MAX(current_price), 0) priceMax FROM products"),
      pool.query<RowDataPacket[]>(`SELECT COUNT(*) total FROM products ${where.sql}`, where.params),
      pool.query<RowDataPacket[]>(`SELECT COUNT(*) total, AVG(COALESCE(ml_score,0)) avgScore, COUNT(DISTINCT brand) brands, SUM(COALESCE(ml_score,0)>=90) luxury, SUM(LOWER(COALESCE(stock_status,'')) IN ('in_stock','instock')) inStock FROM products ${where.sql}`, where.params),
      pool.query<RowDataPacket[]>(`SELECT COALESCE(current_price,0) price FROM products ${where.sql} ORDER BY price`, where.params),
      pool.query<RowDataPacket[]>(`SELECT ${productFields} FROM products ${where.sql} ORDER BY ml_score DESC, reviews_count DESC LIMIT 12`, where.params),
      pool.query<RowDataPacket[]>(`SELECT COALESCE(product_name,'Untitled') name, COALESCE(brand,'Unknown') brand, COALESCE(current_price,0) price, COALESCE(ml_score,0) score, COALESCE(reviews_count,0) reviews, COALESCE(cluster_id,0) cluster FROM products ${where.sql} ORDER BY product_id LIMIT 700`, where.params),
      pool.query<RowDataPacket[]>(`SELECT CASE WHEN current_price < 50 THEN 'Under $50' WHEN current_price < 100 THEN '$50–$100' WHEN current_price < 200 THEN '$100–$200' WHEN current_price < 500 THEN '$200–$500' ELSE '$500+' END band, COUNT(*) count, AVG(COALESCE(ml_score,0)) avgScore FROM products ${where.sql} GROUP BY band ORDER BY MIN(current_price)`, where.params),
      pool.query<RowDataPacket[]>(`SELECT CONCAT('Cluster ',COALESCE(cluster_id,0)) cluster, COUNT(*) count, AVG(COALESCE(ml_score,0)) avgScore FROM products ${where.sql} GROUP BY cluster_id ORDER BY cluster_id`, where.params),
      pool.query<RowDataPacket[]>(`SELECT COALESCE(product_name,'Untitled') name, pca_x x, pca_y y, COALESCE(cluster_id,0) cluster, COALESCE(ml_score,0) score FROM products ${where.sql} AND pca_x IS NOT NULL AND pca_y IS NOT NULL ORDER BY product_id LIMIT 900`, where.params),
      pool.query<RowDataPacket[]>(`SELECT ${productFields} FROM products ${where.sql} AND persona_json IS NOT NULL AND persona_json <> '' ORDER BY ml_score DESC LIMIT 30`, where.params),
      pool.query<RowDataPacket[]>(`SELECT COALESCE(brand,'Unknown') brand, COUNT(*) products, AVG(COALESCE(ml_score,0)) avgScore, AVG(COALESCE(current_price,0)) avgPrice, SUM(COALESCE(reviews_count,0)) reviews FROM products ${where.sql} GROUP BY brand ORDER BY avgScore DESC LIMIT 20`, where.params),
      pool.query<RowDataPacket[]>(`SELECT ${productFields} FROM products ${where.sql} ORDER BY ml_score DESC, product_id LIMIT ? OFFSET ?`, [...where.params, filters.pageSize, offset]),
      readCorrelations(),
    ]);

    const prices = pricesResult[0].map((row) => Number(row.price));
    const middle = Math.floor(prices.length / 2);
    const medianPrice = prices.length ? (prices.length % 2 ? prices[middle] : (prices[middle - 1] + prices[middle]) / 2) : 0;
    const kpi = kpiResult[0][0] ?? {};
    const total = Number(countResult[0][0]?.total ?? 0);
    const personas = (personaResult[0] as Product[]).map(parsePersona).filter((item): item is Persona => Boolean(item)).slice(0, 6);
    const priceMax = Math.ceil(Number(maxPriceResult[0][0]?.priceMax ?? 0));

    const payload: DashboardData = {
      generatedAt: new Date().toISOString(),
      filters: { brands: metaResult[0].map((row) => String(row.brand)), priceMax },
      kpis: { total, avgScore: Number(kpi.avgScore ?? 0), brands: Number(kpi.brands ?? 0), luxury: Number(kpi.luxury ?? 0), medianPrice, inStock: Number(kpi.inStock ?? 0) },
      topPicks: topResult[0] as Product[],
      marketScatter: scatterResult[0] as DashboardData["marketScatter"],
      priceBands: bandResult[0] as DashboardData["priceBands"],
      clusters: clusterResult[0] as DashboardData["clusters"],
      styleMap: styleResult[0] as DashboardData["styleMap"],
      personas,
      brandStats: brandResult[0] as DashboardData["brandStats"],
      correlations,
      products: productsResult[0] as Product[],
      pagination: { page: filters.page, pageSize: filters.pageSize, total, pages: Math.max(1, Math.ceil(total / filters.pageSize)) },
    };
    return NextResponse.json(payload);
  } catch (error) {
    console.error("Dashboard API error", error);
    return NextResponse.json({ error: "Unable to load dashboard data. Check the database configuration." }, { status: 500 });
  }
}
