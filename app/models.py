from app import db, login_manager, bcrypt
from flask_login import UserMixin
from datetime import datetime
import random, string

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def gen_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class User(UserMixin, db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=True)
    google_id  = db.Column(db.String(200), nullable=True)
    picture    = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    quizzes    = db.relationship('Quiz', backref='creator', lazy=True)
    attempts   = db.relationship('Attempt', backref='user', lazy=True)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)


class Quiz(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    code        = db.Column(db.String(10), unique=True, default=gen_code)
    creator_id  = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    time_limit  = db.Column(db.Integer, default=0)
    user_limit  = db.Column(db.Integer, default=0)
    is_active   = db.Column(db.Boolean, default=True)
    questions   = db.relationship('Question', backref='quiz', lazy=True, cascade='all, delete-orphan')
    attempts    = db.relationship('Attempt', backref='quiz', lazy=True, cascade='all, delete-orphan')


class Question(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    quiz_id  = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    text     = db.Column(db.Text, nullable=False)
    order    = db.Column(db.Integer, default=0)
    options  = db.relationship('Option', backref='question', lazy=True, cascade='all, delete-orphan')


class Option(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    text        = db.Column(db.String(300), nullable=False)
    is_correct  = db.Column(db.Boolean, default=False)


class Attempt(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    quiz_id     = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score       = db.Column(db.Float, default=0)
    total       = db.Column(db.Float, default=0)
    started_at  = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    answers     = db.relationship('Answer', backref='attempt', lazy=True, cascade='all, delete-orphan')


class Answer(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    attempt_id  = db.Column(db.Integer, db.ForeignKey('attempt.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    selected_id = db.Column(db.Integer, db.ForeignKey('option.id'), nullable=True)
    is_correct  = db.Column(db.Boolean, default=False)
    question    = db.relationship('Question', foreign_keys=[question_id])