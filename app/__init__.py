from flask import Flask, redirect, url_for, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect, CSRFError
from authlib.integrations.flask_client import OAuth
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()
oauth = OAuth()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    oauth.init_app(app)

    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    login_manager.login_view = 'auth.login'

    with app.app_context():
        from app import models
        from app.auth import auth_bp
        from app.quiz import quiz_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(quiz_bp)

        db.create_all()

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('quiz.dashboard'))
        return render_template('index.html')

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash('Your session expired. Please try again.', 'warning')
        return redirect(request.referrer or url_for('auth.login'))

    return app