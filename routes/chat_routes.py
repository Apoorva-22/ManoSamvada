from flask import Blueprint, request, jsonify, session, redirect, render_template

from services.db_service import get_db
from services.emotion_service import detect_emotion
from services.crisis_service import check_crisis
from services.llm_service import get_llm_response, generate_topic

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat-page")
def chat_page():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html")

# 🔥 START SESSION
@chat_bp.route("/start-session")
def start_session():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    user_id = session.get("user")
    if user_id == "guest":
        user_id = None 

    cursor.execute(
        "INSERT INTO conversation_session (user_id) VALUES (%s)",
        (user_id,)
    )
    db.commit()

    session["chat_session"] = cursor.lastrowid

    cursor.close()
    db.close()

    return jsonify({"success": True})


# 🤖 CHAT
@chat_bp.route("/chat", methods=["POST"])
def chat():

    if "user" not in session:
        return jsonify({"reply": "Unauthorized"})

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if not session.get("chat_session"):

        cursor.execute(
            "INSERT INTO conversation_session (user_id) VALUES (%s)",
            (session.get("user"),)
        )
        db.commit()

        session["chat_session"] = cursor.lastrowid
    msg = request.json["message"].strip()

    emotion = detect_emotion(msg)
    crisis_level = check_crisis(msg)

    if crisis_level == "high":
        reply = """
    I'm really glad you said that instead of keeping it inside.

    Please don't go through this alone right now.

    📞 Tele-MANAS: 14416  
    📞 AASRA: +91 22 2754 6669  

    If someone you trust is available, please call/text them right now.
    """

    elif crisis_level == "medium":
        reply = """
    That sounds really heavy right now.

    Are you feeling unsafe, or is it more emotional exhaustion and overwhelm?
    """

    else:
        reply = get_llm_response(msg, emotion)
    # 🔥 SAVE CHAT
    cursor.execute("""
        INSERT INTO chat_log
        (session_id, message_text, bot_response, emotion_label, sentiment_score, is_crisis_flag)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (
    session["chat_session"],
    msg,
    reply,
    emotion,
    0.5,
    True if crisis_level else False
)
    )

    db.commit()

    # 🔥 TOPIC GENERATION (FIXED LOGIC)
    # 🔥 TOPIC GENERATION (FINAL CLEAN VERSION)
    cursor.execute("""
        SELECT topic FROM conversation_session 
        WHERE session_id=%s
    """, (session["chat_session"],))

    result = cursor.fetchone()

    if (not result) or (result and not result["topic"]):

        cursor.execute("""
            SELECT message_text 
            FROM chat_log
            WHERE session_id=%s
            ORDER BY timestamp ASC
            LIMIT 4
        """, (session["chat_session"],))

        msgs = [row["message_text"] for row in cursor.fetchall()]

        if len(msgs) >= 3:

            combined = " ".join(msgs)

            topic = generate_topic(combined)

            # 🔥 FALLBACK (IMPORTANT)
            if not topic:
                topic = msgs[0][:20]

            print("Generated topic:", topic)

            cursor.execute("""
                UPDATE conversation_session
                SET topic=%s
                WHERE session_id=%s
            """, (topic, session["chat_session"]))

            db.commit()

    # topic fetch karke bhej
            cursor.execute("""
            SELECT topic FROM conversation_session
            WHERE session_id=%s
        """, (session["chat_session"],))

    topic_row = cursor.fetchone()
    topic = topic_row["topic"] if topic_row else None
    cursor.close()
    db.close()

    return jsonify({
        "reply": reply,
        "topic": topic
    })


@chat_bp.route("/get-user")
def get_user():

    if "user" not in session:
        return {"name": "Guest", "username": "guest", "joined": ""}

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT name, username, email, created_at
        FROM user
        WHERE user_id = %s
    """, (session["user"],))

    user = cursor.fetchone()

    cursor.close()
    db.close()

    if not user:
        return {"name": "User", "username": "user", "joined": ""}

    return {
    "name": user["name"] if user["name"] else user["username"],
    "username": user["username"],
    "email": user["email"],   # ✅ NEW
    "joined": str(user["created_at"])
}

@chat_bp.route("/get-session/<int:session_id>")
def get_session(session_id):

    if "user" not in session:
        return jsonify([])

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT message_text, bot_response
        FROM chat_log
        WHERE session_id=%s
        ORDER BY timestamp ASC
    """, (session_id,))

    chats = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(chats)

@chat_bp.route("/switch-session/<int:session_id>")
def switch_session(session_id):

    if "user" not in session:
        return jsonify({"error": "Unauthorized"})

    session["chat_session"] = session_id

    return jsonify({"success": True})


@chat_bp.route("/sessions")
def get_sessions():

    if "user" not in session:
        return jsonify([])

    db = get_db()
    cursor = db.cursor(dictionary=True)

    user_id = session.get("user")

    if user_id == "guest":
        return jsonify([])   # 🔥 guest ke liye empty
    else:
        cursor.execute("""
            SELECT session_id, topic
            FROM conversation_session
            WHERE user_id = %s 
            ORDER BY session_id DESC
        """, (user_id,))

    sessions = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(sessions)

@chat_bp.route("/search-sessions", methods=["GET"])
def search_sessions():

    query = request.args.get("q", "").lower()

    db = get_db()
    cursor = db.cursor(dictionary=True)

    user_id = session.get("user")

    cursor.execute("""
        SELECT DISTINCT cs.session_id, cs.topic
        FROM conversation_session cs
        JOIN chat_log cl ON cs.session_id = cl.session_id
        WHERE cs.user_id=%s
        AND (
            LOWER(cl.message_text) LIKE %s
            OR LOWER(cl.bot_response) LIKE %s
            OR LOWER(cs.topic) LIKE %s
        )
    """, (
        user_id,
        f"%{query}%",
        f"%{query}%",
        f"%{query}%"
    ))

    results = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(results)