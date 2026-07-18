from flask import Blueprint, request, jsonify, session, redirect, render_template
from services.db_service import get_db
from psycopg2.extras import RealDictCursor

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/admin/analytics")
def analytics():

    if "admin" not in session:
        return jsonify({"error": "Unauthorized"})

    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)

    username = request.args.get("users")

    # DEFAULT VALUES 
    sessions = 0
    chats = 0
    crisis = 0
    emotions = []
    daily_data = []

    # USER SPECIFIC
    if username:

        cursor.execute("SELECT user_id FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"})

        user_id = user["user_id"]

        # sessions
        cursor.execute("""
            SELECT COUNT(DISTINCT session_id) as total
            FROM conversation_session
            WHERE user_id=%s
        """, (user_id,))
        sessions = cursor.fetchone()["total"]

        # chats
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM chat_log cl
            JOIN conversation_session cs ON cl.session_id = cs.session_id
            WHERE cs.user_id=%s
        """, (user_id,))
        chats = cursor.fetchone()["total"]

        # crisis
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM chat_log cl
            JOIN conversation_session cs ON cl.session_id = cs.session_id
            WHERE cs.user_id=%s AND cl.is_crisis_flag=1
        """, (user_id,))
        crisis = cursor.fetchone()["total"]

        # emotions
        cursor.execute("""
            SELECT emotion_label, COUNT(*) as count
            FROM chat_log cl
            JOIN conversation_session cs ON cl.session_id = cs.session_id
            WHERE cs.user_id=%s
            GROUP BY emotion_label
        """, (user_id,))
        emotions = cursor.fetchall()

        # daily
        cursor.execute("""
            SELECT DATE(cl.timestamp) as date, COUNT(*) as count
            FROM chat_log cl
            JOIN conversation_session cs ON cl.session_id = cs.session_id
            WHERE cs.user_id=%s
            GROUP BY DATE(cl.timestamp)
            ORDER BY date
        """, (user_id,))
        daily_data = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify({
    "username": request.args.get("user"),
    "sessions": sessions,
    "chats": chats,
    "crisis": crisis,
    "emotions": emotions,
    "daily": daily
})


@analytics_bp.route("/admin/analytics-page")
def analytics_page():
    if "admin" not in session:
        return redirect("/admin/login")
    
    return render_template("admin_analytics.html")

@analytics_bp.route("/user/analytics")
def user_analytics_page():

    if "user" not in session:
        return redirect("/login")

    return render_template("user_analytics.html")


@analytics_bp.route("/user/analytics-data")
def user_analytics_data():

    try:

        if "user" not in session:
            return jsonify({"error": "Unauthorized"})

        db = get_db()
        cursor = db.cursor(cursor_factory=RealDictCursor)

        # ================= GUEST MODE =================
        if session["user"] == "guest":

            session_id = session.get("chat_session")

            if not session_id:
                return jsonify({
                    "sessions": 0,
                    "chats": 0,
                    "emotions": [],
                    "crisis": 0,
                    "daily": []
                })

            # chats
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM chat_log
                WHERE session_id=%s
            """, (session_id,))
            chats = cursor.fetchone()["total"]

            # emotions
            cursor.execute("""
                SELECT emotion_label, COUNT(*) as count
                FROM chat_log
                WHERE session_id=%s
                GROUP BY emotion_label
            """, (session_id,))
            emotions = cursor.fetchall()

            # crisis
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM chat_log
                WHERE session_id=%s
                AND is_crisis_flag = TRUE
            """, (session_id,))
            crisis = cursor.fetchone()["total"]

            # daily
            cursor.execute("""
                SELECT
                    TO_CHAR(DATE(timestamp), 'YYYY-MM-DD') as date,
                    COUNT(*) as count
                FROM chat_log
                WHERE session_id=%s
                GROUP BY DATE(timestamp)
                ORDER BY DATE(timestamp)
            """, (session_id,))
            daily = cursor.fetchall()

            cursor.close()
            db.close()

            return jsonify({
                "sessions": 1,
                "chats": chats,
                "emotions": emotions,
                "crisis": crisis,
                "daily": daily
            })

        user_id = session["user"]

        # sessions
        cursor.execute("""
            SELECT COUNT(DISTINCT cs.session_id) as total
            FROM conversation_session cs
            JOIN chat_log cl
            ON cs.session_id = cl.session_id
            WHERE cs.user_id=%s
        """, (user_id,))
        sessions = cursor.fetchone()["total"]

        # chats
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM chat_log cl
            JOIN conversation_session cs
            ON cl.session_id = cs.session_id
            WHERE cs.user_id=%s
        """, (user_id,))
        chats = cursor.fetchone()["total"]

        # emotions
        cursor.execute("""
            SELECT emotion_label, COUNT(*) as count
            FROM chat_log cl
            JOIN conversation_session cs
            ON cl.session_id = cs.session_id
            WHERE cs.user_id=%s
            GROUP BY emotion_label
        """, (user_id,))
        emotions = cursor.fetchall()

        # crisis
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM chat_log cl
            JOIN conversation_session cs
            ON cl.session_id = cs.session_id
            WHERE cs.user_id=%s
            AND cl.is_crisis_flag = TRUE
        """, (user_id,))
        crisis = cursor.fetchone()["total"]

        # daily
        cursor.execute("""
            SELECT
                TO_CHAR(DATE(cl.timestamp), 'YYYY-MM-DD') as date,
                COUNT(*) as count
            FROM chat_log cl
            JOIN conversation_session cs
            ON cl.session_id = cs.session_id
            WHERE cs.user_id=%s
            GROUP BY DATE(cl.timestamp)
            ORDER BY DATE(cl.timestamp)
        """, (user_id,))
        daily = cursor.fetchall()

        cursor.close()
        db.close()

        return jsonify({
            "sessions": sessions,
            "chats": chats,
            "emotions": emotions,
            "crisis": crisis,
            "daily": daily
        })

    except Exception as e:

        print("ANALYTICS ERROR:", str(e))

        return jsonify({
            "error": str(e)
        }), 500
