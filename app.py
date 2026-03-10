from flask import Flask
from flask_cors import CORS

from routes.auth_routes import auth_bp
from routes.product_routes import product_bp
from routes.pantry_routes import pantry_bp
from routes.recipe_routes import recipe_bp


def create_app():
    app = Flask(__name__)

    CORS(
        app,
        resources={
            r"/*": {
                "origins": ["*"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Accept", "Authorization"],
                "max_age": 3600,
            }
        },
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(pantry_bp)
    app.register_blueprint(recipe_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
