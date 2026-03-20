from flask import Flask
from flask_cors import CORS
import jwt
from datetime import timedelta
from routes.auth import auth
from routes.doctors import doctors_bp
from flask import send_from_directory
from routes.payment import payment_bp
from routes.appointments import appointments_bp
from routes.users import users_bp
from routes.contact import contact_bp
from routes.ai_routes import ai_bp
from routes.admin import admin_bp



app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = "care-nova-super-secret-key"


app.register_blueprint(auth)

app.register_blueprint(ai_bp)

app.register_blueprint(doctors_bp)

app.register_blueprint(users_bp)

app.register_blueprint(payment_bp)

app.register_blueprint(appointments_bp)

app.register_blueprint(contact_bp)

app.register_blueprint(admin_bp)


@app.route("/")
def home():
    return {"message": "Smart Health API Running"}


@app.route("/uploads/<path:filename>")
def uploaded_files(filename):
    return send_from_directory("uploads", filename)


if __name__ == "__main__":
    app.run(debug=True)
