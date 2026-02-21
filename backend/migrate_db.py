# migrate.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        sslmode='require'
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            api_key VARCHAR(64) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            original_url TEXT NOT NULL,
            short_code VARCHAR(10) UNIQUE NOT NULL,
            clicks INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            max_clicks INTEGER,
            blocked_countries TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            id SERIAL PRIMARY KEY,
            url_id INTEGER NOT NULL REFERENCES urls(id) ON DELETE CASCADE,
            clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address VARCHAR(45),
            country VARCHAR(2),
            city VARCHAR(100),
            region VARCHAR(100),
            isp VARCHAR(200),
            lat FLOAT,
            lon FLOAT,
            device_type VARCHAR(50),
            browser VARCHAR(50),
            os VARCHAR(50),
            user_agent TEXT,
            referer TEXT
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Supabase migration completed")

if __name__ == '__main__':
    migrate()