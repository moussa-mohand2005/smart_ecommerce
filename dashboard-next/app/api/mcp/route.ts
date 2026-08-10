import { NextRequest, NextResponse } from "next/server";
import type { RowDataPacket } from "mysql2";
import { pool } from "@/lib/db";

const tools = [
  { name: "get_top_shoes", description: "Fetch the highest-scoring enriched products.", parameters: { limit: "integer from 1 to 20" } },
  { name: "analyze_cluster", description: "Return summary statistics for one style cluster.", parameters: { cluster_id: "non-negative integer" } },
];

export async function GET() {
  return NextResponse.json({ tools });
}

export async function POST(request: NextRequest) {
  try {
    const { name, params = {} } = await request.json();
    if (name === "get_top_shoes") {
      const limit = Math.min(20, Math.max(1, Number.parseInt(params.limit ?? "5", 10) || 5));
      const [rows] = await pool.query<RowDataPacket[]>("SELECT product_name, brand, ml_score FROM products WHERE is_enriched=TRUE ORDER BY ml_score DESC LIMIT ?", [limit]);
      return NextResponse.json({ tool: name, result: rows, audit: { validated: true, executedAt: new Date().toISOString() } });
    }
    if (name === "analyze_cluster") {
      const clusterId = Number.parseInt(params.cluster_id, 10);
      if (!Number.isInteger(clusterId) || clusterId < 0) return NextResponse.json({ error: "Invalid cluster_id." }, { status: 400 });
      const [rows] = await pool.execute<RowDataPacket[]>("SELECT AVG(ml_score) avg_score, AVG(current_price) avg_price, COUNT(*) count FROM products WHERE cluster_id=?", [clusterId]);
      return NextResponse.json({ tool: name, result: rows[0], audit: { validated: true, executedAt: new Date().toISOString() } });
    }
    return NextResponse.json({ error: "Unknown tool." }, { status: 400 });
  } catch (error) {
    console.error("MCP simulation error", error);
    return NextResponse.json({ error: "Tool execution failed." }, { status: 500 });
  }
}
