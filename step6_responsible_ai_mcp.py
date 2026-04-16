import os
import json
import pymysql
from dotenv import load_dotenv

load_dotenv()

class ShoeMCPServer:
    """
    A simplified MCP Server implementation for the Smart Shoe project.
    Exposes controlled 'tools' for the agent to interact with the shoe database.
    """
    
    def __init__(self):
        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASS", ""),
            "database": os.getenv("DB_NAME", "smart_ecommerce"),
        }

    def _get_connection(self):
        return pymysql.connect(**self.db_config)

    def list_tools(self):
        """Standard MCP method to list available tools."""
        return [
            {
                "name": "get_top_shoes",
                "description": "Fetch the highest rated shoes based on ML Score.",
                "parameters": {"limit": "number of items to return"}
            },
            {
                "name": "analyze_cluster",
                "description": "Get summary statistics for a specific style cluster.",
                "parameters": {"cluster_id": "ID of the cluster to analyze"}
            }
        ]

    def call_tool(self, name, params):
        """Responsible tool execution with logging and validation."""
        print(f"[MCP LOG] Executing tool: {name} with params: {params}")
        
        if name == "get_top_shoes":
            limit = int(params.get("limit", 5))
            return self._get_top_shoes(limit)
        elif name == "analyze_cluster":
            cluster_id = params.get("cluster_id")
            return self._analyze_cluster(cluster_id)
        else:
            raise ValueError(f"Unknown tool: {name}")

    def _get_top_shoes(self, limit):
        conn = self._get_connection()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                cur.execute("SELECT product_name, brand, ml_score FROM products WHERE is_enriched=TRUE ORDER BY ml_score DESC LIMIT %s", (limit,))
                return cur.fetchall()
        finally:
            conn.close()

    def _analyze_cluster(self, cluster_id):
        conn = self._get_connection()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                cur.execute("SELECT AVG(ml_score) as avg_score, COUNT(*) as count FROM products WHERE cluster_id=%s", (cluster_id,))
                return cur.fetchone()
        finally:
            conn.close()

if __name__ == "__main__":
    
    server = ShoeMCPServer()
    print("Available Tools:", json.dumps(server.list_tools(), indent=2))
    print("\nExecuting Tool 'get_top_shoes':")
    results = server.call_tool("get_top_shoes", {"limit": 3})
    print(json.dumps(results, indent=2))
