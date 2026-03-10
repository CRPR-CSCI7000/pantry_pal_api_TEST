from functools import wraps

import jwt as pyjwt

from config import JWT_EXPIRATION_HOURS, JWT_SECRET
from services.db import get_db_connection


def generate_token(user_id: int) -> str:
    return pyjwt.encode(
        {
            "user_id": user_id,
            "exp": __import__("datetime").datetime.utcnow() + __import__("datetime").timedelta(hours=JWT_EXPIRATION_HOURS),
        },
        JWT_SECRET,
        algorithm="HS256",
    )


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import request, jsonify

        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'success': False, 'error': 'Authentication token is missing', 'status': 'AUTH_ERROR'}), 401

        try:
            data = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            current_user_id = data['user_id']

            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'error': 'Database connection failed', 'status': 'DB_ERROR'}), 503

            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE userID = %s", (current_user_id,))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if not user:
                return jsonify({'success': False, 'error': 'User not found', 'status': 'AUTH_ERROR'}), 401

        except pyjwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'Authentication token has expired', 'status': 'AUTH_ERROR'}), 401
        except pyjwt.InvalidTokenError:
            return jsonify({'success': False, 'error': 'Invalid authentication token', 'status': 'AUTH_ERROR'}), 401

        return f(current_user_id, *args, **kwargs)

    return decorated
