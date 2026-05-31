from flask import Blueprint, request, jsonify, session, redirect, render_template, Response,url_for
from services.db_service import get_db
from werkzeug.security import check_password_hash
from psycopg2.extras import RealDictCursor


admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/debug-login")
def debug_login():

    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        "SELECT * FROM admin WHERE username=%s",
        ("admin",)
    )

    admin = cursor.fetchone()

    ok = check_password_hash(
        admin["password_hash"],
        "Admin@123"
    )

    cursor.close()
    db.close()

    return jsonify({
        "username": admin["username"],
        "password_matches": ok
    })
    
@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "GET":
        return render_template("admin_login.html")  # 🔥 page show

    # POST logic
    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)

    data = request.get_json(force=True)

    cursor.execute("SELECT * FROM admin WHERE username=%s", (data["username"],))
    admin = cursor.fetchone()

    if admin and check_password_hash(admin["password_hash"], data["password"]):
        session["admin"] = admin["admin_id"]
        return jsonify({"success": True})

    return jsonify({"success": False})

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

    cursor.execute("SELECT COUNT(*) as count FROM chat_log WHERE is_crisis_flag=1")
    result = cursor.fetchone()

    cursor.close()
    db.close()

    return jsonify({"count": result["count"]})

# 📥 EXPORT CSV
@admin_bp.route("/admin/export")
def export():

    if "admin" not in session:
        return "Unauthorized", 403

    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT u.username, cs.session_id,
               ch.message_text, ch.bot_response,
               ch.emotion_label, ch.is_crisis_flag, ch.timestamp
        FROM chat_log ch
        JOIN conversation_session cs ON ch.session_id = cs.session_id
        JOIN users u ON cs.user_id = u.user_id
    """)

    if cursor.with_rows:
        rows = cursor.fetchall()
    else:
        rows = []

    cursor.close()
    db.close()

    # 🔥 CSV generate
    def generate():
        yield "username,session_id,message,bot_response,emotion,crisis,timestamp\n"
        for row in rows:
            yield f"{row['username']},{row['session_id']},{row['message_text']},{row['bot_response']},{row['emotion_label']},{row['is_crisis_flag']},{row['timestamp']}\n"

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=chat_logs.csv"})


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
