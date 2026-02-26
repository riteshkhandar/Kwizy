from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange

class RegisterForm(FlaskForm):
    name     = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email    = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm  = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit   = SubmitField('Register')

class LoginForm(FlaskForm):
    email    = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit   = SubmitField('Login')



class QuizForm(FlaskForm):
    title       = StringField('Quiz Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    time_limit  = IntegerField('Time Limit (minutes)', validators=[Optional(), NumberRange(min=0, message='Cannot be negative')], default=0)
    user_limit  = IntegerField('User Limit', validators=[Optional(), NumberRange(min=0, message='Cannot be negative')], default=0)
    submit      = SubmitField('Create Quiz')