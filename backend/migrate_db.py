# init_railway.py
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def init_railway():
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    cursor = conn.cursor()
    
    # Сначала users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            api_key VARCHAR(64) UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME NULL
        )
    """)
    print("✅ users table created")
    
    # Потом urls (ссылается на users)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            original_url TEXT NOT NULL,
            short_code VARCHAR(10) UNIQUE NOT NULL,
            clicks INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NULL,
            max_clicks INT NULL,
            blocked_countries TEXT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("✅ urls table created")
    
    # Потом analytics (ссылается на urls)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            url_id INT NOT NULL,
            clicked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
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
            referer TEXT,
            FOREIGN KEY (url_id) REFERENCES urls(id) ON DELETE CASCADE
        )
    """)
    print("✅ analytics table created")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("🎉 Railway database initialized successfully!")

if __name__ == '__main__':
    init_railway()