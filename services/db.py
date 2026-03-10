import psycopg2

from config import RAILWAY_ENVIRONMENT, DATABASE_URL, DB_CONFIG


def get_db_connection():
    """Get a connection to the PostgreSQL database."""
    try:
        # If running on Railway, use their provided DATABASE_URL when available
        if RAILWAY_ENVIRONMENT:
            if DATABASE_URL:
                return psycopg2.connect(DATABASE_URL)

            # Fallback to explicit Railway environment variables
            return psycopg2.connect(
                dbname=DB_CONFIG['dbname'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
            )

        # Local development
        return psycopg2.connect(
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
        )
    except Exception as e:
        print(f"Database connection error: {e}")
        return None
