# Flask uygulama ayarları
class Config:
    # Uygulama ayarları
    SECRET_KEY = 'your_secret_key_here'
    DEBUG = False
    TESTING = False
    
    # API ayarları
    FOOTBALL_API_KEY = 'your_football_api_key_here'
    FOOTBALL_API_BASE_URL = 'https://api.football-data.org/v4'
    
    # Veritabanı ayarları
    DATABASE_URL = 'postgresql://username:password@localhost:5432/dbname'
    
    # Model ayarları
    MODEL_PATH = 'app/models'
    DATA_PATH = 'app/data'

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    
class TestingConfig(Config):
    TESTING = True
    DEBUG = True

# Kullanılabilir konfigürasyonlar
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 