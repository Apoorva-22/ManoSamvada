from flask import Blueprint, request, jsonify, session, redirect, render_template, Response,url_for
from services.db_service import get_db
from werkzeug.security import check_password_hash
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/setup")
def admin_setup():

    try:

        db = get_db()
        cursor = db.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT * FROM admin WHERE username=%s",
            ("admin",)
        )

        existing = cursor.fetchone()

        hashed = generate_password_hash("Admin@123")

        if existing:

            cursor.execute("""
                UPDATE admin
                SET
                    password_hash=%s,
                    role=%s
                WHERE username=%s
            """, (
                hashed,
                "admin",
                "admin"
            ))

        else:

            cursor.execute("""
                INSERT INTO admin
                (username, password_hash, role)
                VALUES (%s, %s, %s)
            """, (
                "admin",
                hashed,
                "admin"
            ))

        db.commit()

        cursor.close()
        db.close()

        return "ADMIN READY"

    except Exception as e:

        return f"ERROR: {str(e)}"
    
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
