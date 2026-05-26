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

from services.db_service import get_db
from psycopg2.extras import RealDictCursor


def init_db():
    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS "user" (
        user_id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        username VARCHAR(100) UNIQUE,
        email VARCHAR(255) UNIQUE,
        password_hash TEXT,
        dob DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS conversation_session (
        session_id SERIAL PRIMARY KEY,
        user_id VARCHAR(100),
        topic TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS crisis_keyword (
        keyword_id SERIAL PRIMARY KEY,
        keyword_text TEXT,
        severity_level VARCHAR(20),
        admin_id INT
    );

    CREATE TABLE IF NOT EXISTS chat_log (
        chat_id SERIAL PRIMARY KEY,
        session_id INT,
        message_text TEXT,
        bot_response TEXT,
        emotion_label VARCHAR(50),
        sentiment_score FLOAT,
        is_crisis_flag BOOLEAN,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS admin (
        admin_id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE,
        password_hash TEXT
    );
    """)

    cursor.execute("""
    ALTER TABLE "user"
    ADD COLUMN IF NOT EXISTS name VARCHAR(100);

    ALTER TABLE "user"
    ADD COLUMN IF NOT EXISTS username VARCHAR(100);

    ALTER TABLE "user"
    ADD COLUMN IF NOT EXISTS email VARCHAR(255);

    ALTER TABLE "user"
    ADD COLUMN IF NOT EXISTS password_hash TEXT;

    ALTER TABLE "user"
    ADD COLUMN IF NOT EXISTS dob DATE;

    ALTER TABLE "user"
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

    ALTER TABLE conversation_session
    ADD COLUMN IF NOT EXISTS topic TEXT;
    """)

    db.commit()

    cursor.close()
    db.close()


init_db()

app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(analytics_bp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
