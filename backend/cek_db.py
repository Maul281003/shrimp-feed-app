import sqlite3

conn = sqlite3.connect("shrimp.db")
cursor = conn.cursor()
cursor.execute("SELECT email, full_name FROM users")
users = cursor.fetchall()

print("=== DAFTAR USER DI DATABASE ===")
if not users:
    print("(Kosong - belum ada user sama sekali)")
for u in users:
    print(f"Email: {u[0]} | Nama: {u[1]}")
conn.close()