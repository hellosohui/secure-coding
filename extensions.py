# secure-coding/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# DB 연결 객체
db = SQLAlchemy()

# 로그인 관리 객체
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
