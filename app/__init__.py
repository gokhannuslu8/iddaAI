from flask import Flask
from flask_cors import CORS
from app.config.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    
    # Route'ları kaydet
    from app.routes import match_routes
    app.register_blueprint(match_routes.bp)
    
    return app 