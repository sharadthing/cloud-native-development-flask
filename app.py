from flask import Flask
from flask_cors import CORS
from routes import bp as routes_bp

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Register Blueprint
app.register_blueprint(routes_bp)

# Run the Flask application
if __name__ == "__main__":
    try:
        app.run(debug=True)
    except Exception as e:
        print(f"Error running the app: {str(e)}")