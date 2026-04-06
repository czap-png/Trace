from db.client import get_connection

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cur.fetchall()
        for t in tables:
            print(t[0])
            