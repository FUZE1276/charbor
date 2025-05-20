import psycopg2
import os

try:
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        database=os.environ['DB_NAME'],
        port=os.environ.get('DB_PORT', '5432')  # 5432 por defecto si no está
    )
    cursor = conn.cursor()
    print("✅ Conexión a PostgreSQL remota establecida correctamente.")
except Exception as e:
    print("❌ Error al conectar con la base de datos remota:", e)
    conn = None
    cursor = None
