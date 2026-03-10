from flask import Blueprint, request, jsonify
import bcrypt

from auth import generate_token
from services.db import get_db_connection


auth_bp = Blueprint('auth', __name__, url_prefix='/api')


@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        required_fields = ['userFirstName', 'userLastName', 'username', 'email', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'{field} is required', 'status': 'VALIDATION_ERROR'}), 400

        user_first_name = data['userFirstName']
        user_last_name = data['userLastName']
        username = data['username']
        email = data['email']
        password = data['password']

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed', 'status': 'DB_ERROR'}), 503

        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s OR username = %s", (email, username))
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'User with this email or username already exists', 'status': 'DUPLICATE_USER'}), 409

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute(
            "INSERT INTO users (userLastName, userFirstName, username, email, password_hash) VALUES (%s, %s, %s, %s, %s) RETURNING userID",
            (user_last_name, user_first_name, username, email, hashed_password),
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        token = generate_token(user_id)

        return jsonify({'success': True, 'userID': user_id, 'token': token, 'username': username})

    except Exception as e:
        print(f"Signup error: {str(e)}")
        return jsonify({'success': False, 'error': 'Server error', 'status': 'SERVER_ERROR', 'details': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'success': False, 'error': 'Username and password are required', 'status': 'VALIDATION_ERROR'}), 400

        username = data['username']
        password = data['password']

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed', 'status': 'DB_ERROR'}), 503

        cur = conn.cursor()
        cur.execute("SELECT userID, username, password_hash FROM users WHERE username = %s", (username,))
        user = cur.fetchone()

        if not user or not bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Invalid username or password', 'status': 'INVALID_CREDENTIALS'}), 401

        user_id = user[0]
        username = user[1]
        cur.close()
        conn.close()

        token = generate_token(user_id)
        return jsonify({'success': True, 'userID': user_id, 'token': token, 'username': username})

    except Exception as e:
        print(f"Login error: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Server error', 'status': 'SERVER_ERROR', 'details': str(e)}), 500
