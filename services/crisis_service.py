import re
from services.db_service import get_db
from psycopg2.extras import RealDictCursor

def normalize_text(text):
    text = text.lower()

    
    text = re.sub(r"[^\w\s]", "", text)

    text = re.sub(r"(.)\1{2,}", r"\1", text)

    return text.strip()


def check_crisis(msg):
    normalized_msg = normalize_text(msg)

    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT keyword_text, severity_level 
        FROM crisis_keyword
    """)

    keywords = cursor.fetchall()

    cursor.close()
    db.close()

    detected_severity = None

    for k in keywords:
        keyword = normalize_text(k["keyword_text"])

        if keyword in normalized_msg:
            print(f"CRISIS DETECTED -> {keyword}")
            detected_severity = k["severity_level"]
            break

    return detected_severity
