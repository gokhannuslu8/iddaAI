import os
import tempfile

class Config:
    # Uygulama kök dizini
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Veritabanı
    DATABASE_PATH = os.path.join(BASE_DIR, 'app.db')
    
    # Model dosyaları
    MODEL_DIR = os.path.join(BASE_DIR, 'models')
    MODEL_PATH = os.path.join(MODEL_DIR, 'match_predictor.joblib')
    DATA_PATH = os.path.join(MODEL_DIR, 'training_data.csv')
    
    # Flask configs
    JSON_AS_ASCII = False
    JSONIFY_MIMETYPE = "application/json;charset=utf-8"
    
    # API configs
    FOOTBALL_API_KEY = ''
    FOOTBALL_API_BASE_URL = 'http://api.football-data.org/v4'
    
    # ML model configs
    # Geçici dizini kullan
    MODEL_PATH = os.path.join(tempfile.gettempdir(), 'match_prediction_model.pkl')
    DATA_PATH = os.path.join(tempfile.gettempdir(), 'matches.csv')

    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')

    # Diğer ayarlar
    DEBUG = True 