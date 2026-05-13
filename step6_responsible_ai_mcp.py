import json
import os
from datetime import datetime, timezone

import pymysql
from dotenv import load_dotenv

load_dotenv()


class FashionMCPServer:
    """
    Controlled MCP-style server for the Smart Fashion project.
    It exposes a small read-only tool surface with validation, intent logging,
    and least-privilege database queries.
    """

    MAX_LIMIT = 50
    ALLOWED_TOOLS = {"get_top_products", "analyze_cluster", "get_shop_ranking", "get_category_stats"}

    def __init__(self, audit_log_path="mcp_audit.log"):
        self.audit_log_path = audit_log_path
        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASS", ""),
            "database": os.getenv("DB_NAME", "smart_ecommerce"),
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor,
        }

    def _get_connection(self):
        return pymysql.connect(**self.db_config)

    def _audit(self, tool_name, params, status, reason=""):
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": tool_name,
            "params": self._safe_params(params),
            "status": status,
            "reason": reason,
        }
        with open(self.audit_log_path, "a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _safe_params(self, params):
        return {key: value for key, value in dict(params or {}).items() if "key" not in key.lower()}

    def _bounded_limit(self, value, default=5):
        try:
            limit = int(value)
        except (TypeError, ValueError):
            limit = default
        return max(1, min(limit, self.MAX_LIMIT))

    def list_tools(self):
        return [
            {
                "name": "get_top_products",
                "description": "Read-only: fetch highest scored fashion products.",
                "parameters": {"limit": "integer, 1-50", "category": "string, optional (Clothing/Footwear)"},
            },
            {
                "name": "analyze_cluster",
                "description": "Read-only: summarize one style cluster.",
                "parameters": {"cluster_id": "integer"},
            },
            {
                "name": "get_shop_ranking",
                "description": "Read-only: rank shops by average ML score and product count.",
                "parameters": {"limit": "integer, 1-50"},
            },
            {
                "name": "get_category_stats",
                "description": "Read-only: get statistics per product category.",
                "parameters": {},
            },
        ]

    def call_tool(self, name, params=None):
        params = params or {}
        if name not in self.ALLOWED_TOOLS:
            self._audit(name, params, "denied", "unknown tool")
            raise ValueError(f"Unknown or unauthorized tool: {name}")

        try:
            if name == "get_top_products":
                result = self._get_top_products(
                    self._bounded_limit(params.get("limit", 5)),
                    params.get("category")
                )
            elif name == "analyze_cluster":
                result = self._analyze_cluster(int(params["cluster_id"]))
            elif name == "get_shop_ranking":
                result = self._get_shop_ranking(self._bounded_limit(params.get("limit", 10)))
            elif name == "get_category_stats":
                result = self._get_category_stats()
            self._audit(name, params, "allowed")
            return result
        except Exception as exc:
            self._audit(name, params, "failed", str(exc))
            raise

    def _get_top_products(self, limit, category=None):
        if category:
            query = """
                SELECT product_name, brand, category, subcategory, current_price, currency, stock_status, ml_score
                FROM products
                WHERE is_enriched=TRUE AND category=%s
                ORDER BY ml_score DESC
                LIMIT %s
            """
            return self._fetch_all(query, (category, limit))
        else:
            query = """
                SELECT product_name, brand, category, subcategory, current_price, currency, stock_status, ml_score
                FROM products
                WHERE is_enriched=TRUE
                ORDER BY ml_score DESC
                LIMIT %s
            """
            return self._fetch_all(query, (limit,))

    def _analyze_cluster(self, cluster_id):
        query = """
            SELECT cluster_id, AVG(ml_score) AS avg_score, COUNT(*) AS product_count,
                   MIN(current_price) AS min_price, MAX(current_price) AS max_price
            FROM products
            WHERE cluster_id=%s
            GROUP BY cluster_id
        """
        rows = self._fetch_all(query, (cluster_id,))
        return rows[0] if rows else {"cluster_id": cluster_id, "product_count": 0}

    def _get_shop_ranking(self, limit):
        query = """
            SELECT s.shop_name, s.platform, COUNT(p.product_id) AS product_count,
                   AVG(p.ml_score) AS avg_score
            FROM shops s
            JOIN products p ON p.shop_id = s.shop_id
            WHERE p.is_enriched=TRUE
            GROUP BY s.shop_id, s.shop_name, s.platform
            ORDER BY avg_score DESC, product_count DESC
            LIMIT %s
        """
        return self._fetch_all(query, (limit,))

    def _get_category_stats(self):
        query = """
            SELECT category, COUNT(*) AS product_count,
                   AVG(ml_score) AS avg_score, AVG(current_price) AS avg_price
            FROM products
            WHERE is_enriched=TRUE
            GROUP BY category
            ORDER BY product_count DESC
        """
        return self._fetch_all(query, ())

    def _fetch_all(self, query, params):
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
        finally:
            conn.close()


# Backward compatibility alias
ShoeMCPServer = FashionMCPServer


if __name__ == "__main__":
    server = FashionMCPServer()
    print("Available Tools:", json.dumps(server.list_tools(), indent=2))
    print("\nExecuting Tool 'get_top_products':")
    print(json.dumps(server.call_tool("get_top_products", {"limit": 3}), indent=2, default=str))
