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

def connect_db_write(db_path: str):
    """Connect database (write mode)"""
    conn = sqlite3.connect(db_path)
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

@mcp.tool()
async def read_table(db_path: str, table_name: str, limit: int = 10) -> Dict[str, Any]:
    """Read the given table and bring the content"""
    try:
        with connect_db(db_path) as conn:
            cur = conn.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit,))
            rows = [dict(r) for r in cur.fetchall()]
            
            # Sütun isimlerini de al
            column_names = [desc[0] for desc in cur.description] if cur.description else []
            
            return {
                "table": table_name,
                "columns": column_names,
                "rows": rows,
                "count": len(rows)
            }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_out_of_stock(db_path: str, table_name: str) -> Dict[str, Any]:
    """Get ALL items where in_stock=0 (out of stock items)"""
    try:
        with connect_db(db_path) as conn:
            # Önce kaç tane var kontrol et
            count_cur = conn.execute(f"SELECT COUNT(*) FROM {table_name} WHERE in_stock = 0")
            total_count = count_cur.fetchone()[0]
            
            # Sonra hepsini getir
            cur = conn.execute(f"SELECT * FROM {table_name} WHERE in_stock = 0")
            rows = [dict(r) for r in cur.fetchall()]
            
            column_names = [desc[0] for desc in cur.description] if cur.description else []
            
            return {
                "table": table_name,
                "columns": column_names,
                "out_of_stock_items": rows,
                "total_in_db": total_count,
                "returned_count": len(rows),
                "message": f"Found {total_count} out of stock items"
            }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_in_stock(db_path: str, table_name: str) -> Dict[str, Any]:
    """Get ALL items where in_stock=1 (items that are in stock)"""
    try:
        with connect_db(db_path) as conn:
            # Önce kaç tane var kontrol et
            count_cur = conn.execute(f"SELECT COUNT(*) FROM {table_name} WHERE in_stock = 1")
            total_count = count_cur.fetchone()[0]
            
            # Sonra hepsini getir
            cur = conn.execute(f"SELECT * FROM {table_name} WHERE in_stock = 1")
            rows = [dict(r) for r in cur.fetchall()]
            
            column_names = [desc[0] for desc in cur.description] if cur.description else []
            
            return {
                "table": table_name,
                "columns": column_names,
                "in_stock_items": rows,
                "total_in_db": total_count,
                "returned_count": len(rows),
                "message": f"Found {total_count} in stock items"
            }
    except Exception as e:
        return {"error": str(e)}
        
@mcp.tool()
async def add_item( db_path: str, table_name: str,item_name: str,quantity: int = 0,in_stock: int = 0) -> Dict[str, Any]:
    """Add a new item to the table"""
    try:
        with connect_db_write(db_path) as conn:
            # Timestamp otomatik olarak CURRENT_TIMESTAMP ile eklenir
            cur = conn.execute(
                f"""INSERT INTO {table_name} 
                    (item_name, quantity, in_stock, updated_at) 
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
                (item_name, quantity, in_stock)
            )
            conn.commit()
            
            # Eklenen item'ın ID'sini al
            inserted_id = cur.lastrowid
            
            # Eklenen item'ı kontrol et
            check_cur = conn.execute(
                f"SELECT * FROM {table_name} WHERE id = ?",
                (inserted_id,)
            )
            inserted_row = dict(check_cur.fetchone())
            
            return {
                "success": True,
                "message": f"Item '{item_name}' added successfully",
                "inserted_id": inserted_id,
                "inserted_item": inserted_row
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def delete_item(db_path: str, table_name: str,item_name: str) -> Dict[str, Any]:
    """Delete an item from the table by its name"""
    try:
        with connect_db_write(db_path) as conn:
            # Önce item'ın var olup olmadığını kontrol et
            check_cur = conn.execute(
                f"SELECT * FROM {table_name} WHERE item_name = ?",
                (item_name,)
            )
            item = check_cur.fetchone()
            
            if not item:
                return {
                    "success": False,
                    "message": f"Item '{item_name}' not found in table {table_name}"
                }
            
            # Item bilgilerini sakla
            deleted_item = dict(item)
            
            # Item'ı sil
            conn.execute(
                f"DELETE FROM {table_name} WHERE item_name = ?",
                (item_name,)
            )
            conn.commit()
            
            return {
                "success": True,
                "message": f"Item '{item_name}' deleted successfully",
                "deleted_item": deleted_item
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def update_item(db_path: str, table_name: str,item_name: str,new_item_name: str = None,quantity: int = None,in_stock: int = None) -> Dict[str, Any]:
    """Update an existing item in the table by its name"""
    try:
        with connect_db_write(db_path) as conn:
            # Önce item'ın var olup olmadığını kontrol et
            check_cur = conn.execute(
                f"SELECT * FROM {table_name} WHERE item_name = ?",
                (item_name,)
            )
            old_item = check_cur.fetchone()
            
            if not old_item:
                return {
                    "success": False,
                    "message": f"Item '{item_name}' not found in table {table_name}"
                }
            
            # Eski item bilgilerini sakla
            old_item_dict = dict(old_item)
            
            # Güncellenecek alanları belirle
            updates = []
            params = []
            
            if new_item_name is not None:
                updates.append("item_name = ?")
                params.append(new_item_name)
            
            if quantity is not None:
                updates.append("quantity = ?")
                params.append(quantity)
            
            if in_stock is not None:
                updates.append("in_stock = ?")
                params.append(in_stock)
            
            # updated_at her zaman güncellenir
            updates.append("updated_at = CURRENT_TIMESTAMP")
            
            if len(updates) == 1:  # Sadece updated_at varsa
                return {
                    "success": False,
                    "message": "No fields to update"
                }
            
            # UPDATE query'sini oluştur
            update_query = f"UPDATE {table_name} SET {', '.join(updates)} WHERE item_name = ?"
            params.append(item_name)
            
            # Güncelleme yap
            conn.execute(update_query, params)
            conn.commit()
            
            # Güncellenmiş item'ı getir (isim değiştiyse yeni isimle ara)
            search_name = new_item_name if new_item_name else item_name
            updated_cur = conn.execute(
                f"SELECT * FROM {table_name} WHERE item_name = ?",
                (search_name,)
            )
            updated_item = dict(updated_cur.fetchone())
            
            return {
                "success": True,
                "message": f"Item '{item_name}' updated successfully",
                "old_item": old_item_dict,
                "updated_item": updated_item
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP SQLite Reader Service")
    parser.add_argument("--connection_type", type=str, default="http", choices=["http", "stdio"])
    parser.add_argument("--port", type=int, default=3002)
    args = parser.parse_args()

    mcp.port = args.port
    server_type = "sse" if args.connection_type == "http" else "stdio"
    print(f"Starting SQLite Reader on port {args.port} via {args.connection_type}")
    mcp.run(server_type)