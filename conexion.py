import psycopg2

# Conexión a la base de datos PostgreSQL
try:
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",      # Cambia si tu base se llama diferente
        user="postgres",          # Tu usuario de PostgreSQL
        password="THEGHOST7274"   # Tu contraseña de PostgreSQL
    )
    cursor = conn.cursor()
    print("✅ Conexión a PostgreSQL establecida correctamente.")
except Exception as e:
    print("❌ Error al conectar con la base de datos:", e)
    conn = None
    cursor = None
