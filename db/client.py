import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DSN = os.getenv("POSTGRES_DSN", "postgresql://trace:trace_dev@localhost:5432/trace")

def get_connection():
    """Return a synchronous psycopg connection."""
    return psycopg.connect(DSN)

def test_connection():
    """Quick check that we can reach the database."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                print("Database connection successful.")
    except Exception as e:
        print(f"Database connection failed: {e}")

if __name__ == "__main__":
    test_connection()