# migrate_db.py
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def migrate_database():
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'shcut')
    )
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE urls ADD COLUMN blocked_countries TEXT NULL")
        print("Added column: blocked_countries")
    except:
        print("Column blocked_countries already exists")
    
    try:
        cursor.execute("ALTER TABLE urls ADD COLUMN max_clicks INT NULL")
        print("Added column: max_clicks")
    except:
        print("Column max_clicks already exists")
    
    try:
        cursor.execute("ALTER TABLE urls ADD COLUMN expires_at DATETIME NULL")
        print("Added column: expires_at")
    except:
        print("Column expires_at already exists")
    
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
    print("Created analytics table")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Migration completed")

if __name__ == '__main__':
    migrate_database()