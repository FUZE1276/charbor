import psycopg2
import os

import psycopg2

# Conexión a base de datos remota (Clever Cloud)
try:
    conn = psycopg2.connect(
        host='bvwfyr03z7nd6awox7a5-postgresql.services.clever-cloud.com',
        user='us0nxqdxueurk6pgmiyr',
        password='n1vF2qL2ZZI95yT9ipcv3atZuwOYwy',
        database='bvwfyr03z7nd6awox7a5',
        port='50013'
    )
    cursor = conn.cursor()
    print("✅ Conexión a PostgreSQL (remota) establecida correctamente.")
except Exception as e:
    print("❌ Error al conectar con la base de datos:", type(e).__name__, e)
    conn = None
    cursor = None
