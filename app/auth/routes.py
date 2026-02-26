from flask import render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from app.auth import auth_bp
from app.models import User
from app.forms import RegisterForm, LoginForm
from app import db, oauth


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))
        user = User(name=form.name.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('quiz.dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/login/google')
def google_login():
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/login/google/callback')
def google_callback():
    token = oauth.google.authorize_access_token()
    user_info = token['userinfo']

    google_id = user_info['sub']
    email     = user_info['email']
    name      = user_info['name']
    picture   = user_info.get('picture', '')

    user = User.query.filter_by(google_id=google_id).first()

    if not user:
        user = User.query.filter_by(email=email).first()
        if user:
            # Existing email user — link Google account
            user.google_id = google_id
            user.picture   = picture
            db.session.commit()
            flash('Google account linked! Welcome back 👋', 'success')
        else:
            # Brand new user — create account
            user = User(
                name=name,
                email=email,
                google_id=google_id,
                picture=picture
            )
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully! Welcome to QuizApp 🎉', 'success')
    else:
        flash('Logged in with Google!', 'success')

    login_user(user)
    return redirect(url_for('quiz.dashboard'))