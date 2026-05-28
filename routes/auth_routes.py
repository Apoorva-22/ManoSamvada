from flask import Blueprint, render_template, request, jsonify, session, redirect
from services.db_service import get_db
from services.otp_service import send_email_otp, otp_store
from werkzeug.security import generate_password_hash, check_password_hash
import time
from psycopg2.extras import RealDictCursor

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def welcome():
    return render_template("welcome.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json(force=True)

    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM users WHERE username=%s", (data["username"],))
    user = cursor.fetchone()

    cursor.close()
    db.close()

    if user and check_password_hash(user["password_hash"], data["password"]):
        session["user"] = user["user_id"]
        return jsonify({"success": True})

    return jsonify({"success": False})


# 📝 SIGNUP
@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    data = request.get_json(force=True)

    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)

    username = data["username"].lower().strip()
    email = data["email"].lower().strip()

    # 🔍 Username check
    cursor.execute("SELECT * FROM users WHERE LOWER(username)=%s", (username,))
    if cursor.fetchone():
        return jsonify({"success": False, "message": "Username already exists"})

    # 🔍 Email check
    cursor.execute("SELECT * FROM users WHERE LOWER(email)=%s", (email,))
    if cursor.fetchone():
        return jsonify({"success": False, "message": "Email already exists"})

    from werkzeug.security import generate_password_hash
    hashed_password = generate_password_hash(data["password"])

    try:
        cursor.execute("""
            INSERT INTO users (name, username, email, password_hash)
            VALUES (%s, %s, %s, %s)
        """, (
            data["name"],
            username,
            email,
            hashed_password
        ))

        db.commit()

        # 🔥 IMPORTANT: session set
        session["user"] = cursor.lastrowid

    except Exception as e:
        print("ERROR:", e)
        db.rollback()
        return jsonify({
            "success": False,
            "message": "Server error. Try again."
        })

    cursor.close()
    db.close()

    return jsonify({"success": True})

# 📩 OTP SEND
@auth_bp.route("/send-otp", methods=["POST"])
def send_otp():

    email = request.json["email"]

    print("OTP request for:", email)

    try:
        send_email_otp(email)

        print("OTP mail sent successfully")

        return jsonify({
            "success": True,
            "message": "OTP sent"
        })

    except Exception as e:

        print("OTP MAIL ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# ✅ OTP VERIFY
@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json
    record = otp_store.get(data["email"])

    if not record:
        return jsonify({"success": False})

    if time.time() - record["time"] > 300:
        return jsonify({"success": False, "message": "OTP expired"})

    if record["otp"] == data["otp"]:
        return jsonify({"success": True})

    return jsonify({"success": False})


@auth_bp.route("/guest")
def guest():
    session["user"] = "guest"
    return redirect("/chat-page")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")
