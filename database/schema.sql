CREATE DATABASE mental_health;
USE mental_health;

CREATE TABLE chat_log (
    chat_id INT AUTO_INCREMENT PRIMARY KEY,
    message_text TEXT,
    emotion_label VARCHAR(50),
    sentiment_score FLOAT,
    is_crisis_flag BOOLEAN,
    timestamp TIMESTAMP
);