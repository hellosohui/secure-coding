# secure-coding/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(3,80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(6,128)])
    submit   = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit   = SubmitField('Login')

class ProductForm(FlaskForm):
    name        = StringField('Name', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description')
    price       = IntegerField('Price', validators=[DataRequired(), NumberRange(min=0)])
    submit      = SubmitField('Upload')

class MessageForm(FlaskForm):
    content = TextAreaField('Message', validators=[DataRequired(), Length(max=500)])
    submit  = SubmitField('Send')
