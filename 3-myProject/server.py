import argparse
import sqlite3
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("SQLiteReader", host="127.0.0.1", port=3002)


def connect_db(db_path: str):
    """ Connect database (read-only)"""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


@mcp.tool()
async def list_tables(db_path: str) -> Dict[str, Any]:
    """List all the tables in db """
    try:
        with connect_db(db_path) as conn:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cur.fetchall()]
            return {"tables": tables, "count": len(tables)}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP SQLite Reader Service")
    parser.add_argument("--connection_type", type=str, default="http", choices=["http", "stdio"])
    parser.add_argument("--port", type=int, default=3002)
    args = parser.parse_args()

    mcp.port = args.port
    server_type = "sse" if args.connection_type == "http" else "stdio"
    print(f"Starting SQLite Reader on port {args.port} via {args.connection_type}")
    mcp.run(server_type)