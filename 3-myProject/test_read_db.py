import sqlite3

def read_materials_db(db_path="kitchen.db"):
    try:
        # Veritabanına bağlan
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # materials tablosundan verileri al
        cursor.execute("SELECT * FROM materials;")
        rows = cursor.fetchall()

        # Sütun isimlerini al
        column_names = [desc[0] for desc in cursor.description]
        print("Columns:", column_names)
        print("-" * 50)

        # Satırları yazdır
        for row in rows:
            print(row)

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()

# Çalıştır
if __name__ == "__main__":
    read_materials_db()
