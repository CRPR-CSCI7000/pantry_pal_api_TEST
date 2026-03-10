import os

from dotenv import load_dotenv

load_dotenv()

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Go-UPC
GOUPC_API_KEY = os.getenv('GOUPC_API_KEY')

# JWT
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))

# Database
RAILWAY_ENVIRONMENT = bool(os.getenv('RAILWAY_ENVIRONMENT'))
DATABASE_URL = os.getenv('DATABASE_URL')

DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'pantry_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5433'),
}

# API rate limiting for Go-UPC
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '1'))
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '1'))
