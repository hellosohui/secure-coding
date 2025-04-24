# secure-coding/config.py
import os

# 이 파일이 있는 폴더 경로(프로젝트 루트)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 디버그용 시크릿 키 (배포할 땐 환경변수로 설정하세요)
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')

# SQLite DB: 프로젝트 루트의 market.db 파일을 씁니다.
SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'market.db')}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
