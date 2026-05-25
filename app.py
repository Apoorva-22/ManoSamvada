import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

from routes.auth_routes import auth_bp
from routes.chat_routes import chat_bp
from routes.admin_routes import admin_bp
from routes.analytics_routes import analytics_bp

app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(analytics_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
