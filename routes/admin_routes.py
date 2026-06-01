from flask import Blueprint, request, jsonify, session, redirect, render_template, Response,url_for
from services.db_service import get_db
from werkzeug.security import check_password_hash
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "GET":
        return render_template("admin_login.html")

    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)

    data = request.get_json(force=True)

    cursor.execute(
        "SELECT * FROM admin WHERE username=%s",
        (data["username"].strip(),)
    )

    admin = cursor.fetchone()

    if not admin:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Admin not found"
        })

    ok = check_password_hash(
        admin["password_hash"],
        data["password"]
    )

    if not ok:

        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Password mismatch"
        })

    session["admin"] = admin["admin_id"]

    cursor.close()
    db.close()

    return jsonify({
        "success": True
    })
    
# 🔒 ADMIN PAGE
@admin_bp.route("/admin")
def admin():
    if "admin" not in session:
        return redirect("/admin/login")
    return render_template("admin.html")

# 📊 ADMIN DATA
@admin_bp.route("/admin/data")
def admin_data():

    if "admin" not in session:
        return jsonify({"error": "Unauthorized"})

    search = request.args.get("search", "").strip()

    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)

    if search:
        cursor.execute("""
            SELECT 
                cl.session_id,
                cl.message_text,
                cl.bot_response,
                cl.emotion_label,
                cl.timestamp,
                cl.is_crisis_flag,
                u.username
            FROM chat_log cl
            JOIN conversation_session cs 
                ON cl.session_id = cs.session_id
            LEFT JOIN users u 
                ON cs.user_id = u.user_id
            WHERE u.username LIKE %s
            ORDER BY cl.timestamp DESC
        """, (f"%{search}%",))

    else:
        cursor.execute("""
            SELECT 
                cl.session_id,
                cl.message_text,
                cl.bot_response,
                cl.emotion_label,
                cl.timestamp,
                cl.is_crisis_flag,
                u.username
            FROM chat_log cl
            JOIN conversation_session cs 
                ON cl.session_id = cs.session_id
            LEFT JOIN users u 
                ON cs.user_id = u.user_id
            ORDER BY cl.timestamp DESC
        """)

    data = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(data)


# 🔴 CRISIS COUNT
@admin_bp.route("/admin/crisis-count")
def crisis_count():

    if "admin" not in session:
        return jsonify({"error": "Unauthorized"})

    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT COUNT(*) as count
        FROM chat_log
        WHERE is_crisis_flag = TRUE
    """)

    result = cursor.fetchone()

    cursor.close()
    db.close()

    return jsonify({
        "count": result["count"]
    })

# 📥 EXPORT CSV
@admin_bp.route("/admin/export")
def export():

    if "admin" not in session:
        return "Unauthorized", 403

    username = request.args.get("user", "").strip()
    crisis_only = request.args.get("crisis") == "true"

    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT
            u.username,
            cs.session_id,
            ch.message_text,
            ch.bot_response,
            ch.emotion_label,
            ch.is_crisis_flag,
            ch.timestamp
        FROM chat_log ch
        JOIN conversation_session cs
            ON ch.session_id = cs.session_id
        LEFT JOIN users u
            ON cs.user_id = u.user_id
        WHERE 1=1
    """

    params = []

    if username:
        query += " AND u.username=%s"
        params.append(username)

    if crisis_only:
        query += " AND ch.is_crisis_flag=TRUE"

    query += " ORDER BY ch.timestamp DESC"

    cursor.execute(query, tuple(params))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    # filename
    if username and crisis_only:
        filename = f"{username}_crisis.csv"

    elif username:
        filename = f"{username}.csv"

    elif crisis_only:
        filename = "crisis.csv"

    else:
        filename = "chat_logs.csv"

    def generate():

        yield "username,session_id,message,bot_response,emotion,crisis,timestamp\n"

        for row in rows:

            yield (
                f'"{row["username"] or "Guest User"}",'
                f'"{row["session_id"]}",'
                f'"{row["message_text"]}",'
                f'"{row["bot_response"]}",'
                f'"{row["emotion_label"]}",'
                f'"{row["is_crisis_flag"]}",'
                f'"{row["timestamp"]}"\n'
            )

    return Response(
        generate(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            f"attachment; filename={filename}"
        }
    )

@admin_bp.route("/admin/add-keyword", methods=["POST"])
def add_keyword():

    if "admin" not in session:
        return jsonify({"error":"Unauthorized"})

    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)

    data = request.json

    cursor.execute(
        "INSERT INTO crisis_keyword (keyword_text, severity_level) VALUES (%s,%s)",
        (data["keyword"], data["level"])
    )
    db.commit()

    cursor.close()
    db.close()

    return jsonify({"success":True})

@admin_bp.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin/login")

@admin_bp.route("/admin/analytics-page")
def admin_analytics_page():

    if "admin" not in session:
        return redirect("/admin/login")

    username = request.args.get("user", "").strip()

    return render_template(
        "admin_analytics.html",
        username=username
    )

@admin_bp.route("/admin/analytics-data")
def admin_analytics_data():

    if "admin" not in session:
        return jsonify({"error":"Unauthorized"})

    username = request.args.get("user", "").strip()

    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)

    # sessions
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM conversation_session cs
        JOIN users u
        ON cs.user_id = u.user_id
        WHERE u.username=%s
    """, (username,))
    sessions = cursor.fetchone()["total"]

    # chats
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM chat_log cl
        JOIN conversation_session cs
            ON cl.session_id = cs.session_id
        JOIN users u
            ON cs.user_id = u.user_id
        WHERE u.username=%s
    """, (username,))
    chats = cursor.fetchone()["total"]

    # emotions
    cursor.execute("""
        SELECT emotion_label,
               COUNT(*) as count
        FROM chat_log cl
        JOIN conversation_session cs
            ON cl.session_id = cs.session_id
        JOIN users u
            ON cs.user_id = u.user_id
        WHERE u.username=%s
        GROUP BY emotion_label
    """, (username,))
    emotions = cursor.fetchall()

    # crisis
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM chat_log cl
        JOIN conversation_session cs
            ON cl.session_id = cs.session_id
        JOIN users u
            ON cs.user_id = u.user_id
        WHERE u.username=%s
        AND cl.is_crisis_flag = TRUE
    """, (username,))
    crisis = cursor.fetchone()["total"]

    # daily
    cursor.execute("""
        SELECT DATE(cl.timestamp) as date,
               COUNT(*) as count
        FROM chat_log cl
        JOIN conversation_session cs
            ON cl.session_id = cs.session_id
        JOIN users u
            ON cs.user_id = u.user_id
        WHERE u.username=%s
        GROUP BY DATE(cl.timestamp)
        ORDER BY DATE(cl.timestamp)
    """, (username,))
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
