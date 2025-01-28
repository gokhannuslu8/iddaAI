import sqlite3
from config import Config
import os

def init_db():
    # Veritabanı dosyası yoksa oluştur
    if not os.path.exists(Config.DATABASE_PATH):
        print(f"Veritabanı oluşturuluyor: {Config.DATABASE_PATH}")
        
        # Veritabanı bağlantısı
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Matches tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                home_team_id INTEGER NOT NULL,
                away_team_id INTEGER NOT NULL,
                home_goals INTEGER NOT NULL,
                away_goals INTEGER NOT NULL,
                match_date TEXT NOT NULL,
                league_id INTEGER NOT NULL,
                season TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Teams tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                league_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Leagues tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leagues (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                country TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Örnek veriler
        cursor.execute("INSERT INTO leagues (id, name, country) VALUES (?, ?, ?)", 
                      (39, 'Premier League', 'England'))
        cursor.execute("INSERT INTO leagues (id, name, country) VALUES (?, ?, ?)", 
                      (140, 'La Liga', 'Spain'))
        
        # Değişiklikleri kaydet
        conn.commit()
        
        print("Veritabanı başarıyla oluşturuldu!")
        
        # Bağlantıyı kapat
        cursor.close()
        conn.close()
    else:
        print("Veritabanı zaten mevcut.")

if __name__ == '__main__':
    init_db() 