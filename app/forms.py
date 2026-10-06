from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, TextAreaField, DateField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, ValidationError
from app.models import User


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), Length(min=3, max=80)
    ])
    email = StringField('Email', validators=[
        DataRequired(), Email(), Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=6)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class ExpenseForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    amount = FloatField('Amount (₹)', validators=[
        DataRequired(), NumberRange(min=0.01, message='Amount must be positive')
    ])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    payment_method = SelectField('Payment Method', choices=[
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('UPI', 'UPI'),
        ('Net Banking', 'Net Banking'),
        ('Wallet', 'Wallet'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Expense')


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=50)])
    icon = SelectField('Icon', choices=[
        ('tag', 'Tag'),
        ('cart', 'Shopping Cart'),
        ('cup-hot', 'Food & Drink'),
        ('car-front', 'Transport'),
        ('house', 'Housing'),
        ('heart-pulse', 'Health'),
        ('film', 'Entertainment'),
        ('book', 'Education'),
        ('airplane', 'Travel'),
        ('phone', 'Utilities'),
        ('gift', 'Gifts'),
        ('cash-stack', 'Salary/Income'),
        ('three-dots', 'Other')
    ], default='tag')
    color = StringField('Color', validators=[DataRequired(), Length(min=7, max=7)], default='#6c757d')
    submit = SubmitField('Save Category')


class BudgetForm(FlaskForm):
    category_id = SelectField('Category (leave empty for overall)', coerce=int, validators=[Optional()])
    amount = FloatField('Budget Amount (₹)', validators=[
        DataRequired(), NumberRange(min=1, message='Budget must be at least 1')
    ])
    month = SelectField('Month', coerce=int, choices=[
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ], validators=[DataRequired()])
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=2020, max=2035)])
    submit = SubmitField('Set Budget')
