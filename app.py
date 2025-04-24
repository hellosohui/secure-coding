import sqlite3
import uuid
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, g, abort
)
from flask_socketio import SocketIO, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
DATABASE = 'market.db'
socketio = SocketIO(app)

# ────────────────────────────────────────────────────────────────────────────────
# 기존: 데이터베이스 연결 관리, 앱 종료 시 close
# ────────────────────────────────────────────────────────────────────────────────
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ────────────────────────────────────────────────────────────────────────────────
# 수정: init_db에 transaction 테이블 생성 추가
# ────────────────────────────────────────────────────────────────────────────────
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # 사용자 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                bio TEXT
            )
        """)
    
        # 상품 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                price TEXT NOT NULL,
                seller_id TEXT NOT NULL
            )
        """)
        # 신고 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS report (
                id TEXT PRIMARY KEY,
                reporter_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                reason TEXT NOT NULL
            )
        """)
        # ─── 추가된 기능: 거래 기록 테이블 ─────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                amount INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # ─────────────────────────────────────────────────────────────────────────
        db.commit()

# ────────────────────────────────────────────────────────────────────────────────
# 기존: 기본, 회원가입, 로그인, 로그아웃, 대시보드, 프로필, 상품 등록/상세, 신고, 채팅
# ────────────────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db(); cursor = db.cursor()
        cursor.execute("SELECT * FROM user WHERE username = ?", (username,))
        if cursor.fetchone():
            flash('이미 존재하는 사용자명입니다.')
            return redirect(url_for('register'))
        user_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO user (id, username, password) VALUES (?, ?, ?)",
            (user_id, username, password)
        )
        db.commit()
        flash('회원가입이 완료되었습니다. 로그인 해주세요.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db(); cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM user WHERE username = ? AND password = ?",
            (username, password)
        )
        user = cursor.fetchone()
        if user:
            session['user_id'] = user['id']
            flash('로그인 성공!')
            return redirect(url_for('dashboard'))
        else:
            flash('아이디 또는 비밀번호가 올바르지 않습니다.')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('로그아웃되었습니다.')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db(); cursor = db.cursor()
    cursor.execute("SELECT * FROM user WHERE id = ?", (session['user_id'],))
    current_user = cursor.fetchone()
    cursor.execute("SELECT * FROM product")
    all_products = cursor.fetchall()
    return render_template(
        'dashboard.html',
        products=all_products,
        user=current_user
    )

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db(); cursor = db.cursor()
    if request.method == 'POST':
        bio = request.form.get('bio', '')
        cursor.execute(
            "UPDATE user SET bio = ? WHERE id = ?",
            (bio, session['user_id'])
        )
        db.commit()
        flash('프로필이 업데이트되었습니다.')
        return redirect(url_for('profile'))
    cursor.execute("SELECT * FROM user WHERE id = ?", (session['user_id'],))
    current_user = cursor.fetchone()
    return render_template('profile.html', user=current_user)

@app.route('/product/new', methods=['GET', 'POST'])
def new_product():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        db = get_db(); cursor = db.cursor()
        product_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO product "
            "(id, title, description, price, seller_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (product_id, title, description, price, session['user_id'])
        )
        db.commit()
        flash('상품이 등록되었습니다.')
        return redirect(url_for('dashboard'))
    return render_template('new_product.html')

@app.route('/product/<product_id>')
def view_product(product_id):
    db = get_db(); cursor = db.cursor()
    cursor.execute("SELECT * FROM product WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        flash('상품을 찾을 수 없습니다.')
        return redirect(url_for('dashboard'))
    cursor.execute(
        "SELECT * FROM user WHERE id = ?", (product['seller_id'],)
    )
    seller = cursor.fetchone()
    return render_template(
        'view_product.html',
        product=product,
        seller=seller
    )

@app.route('/report', methods=['GET', 'POST'])
def report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        target_id = request.form['target_id']
        reason    = request.form['reason']
        db = get_db(); cursor = db.cursor()
        report_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO report "
            "(id, reporter_id, target_id, reason) "
            "VALUES (?, ?, ?, ?)",
            (report_id, session['user_id'], target_id, reason)
        )
        db.commit()
        flash('신고가 접수되었습니다.')
        return redirect(url_for('dashboard'))
    return render_template('report.html')

@socketio.on('send_message')
def handle_send_message_event(data):
    data['message_id'] = str(uuid.uuid4())
    send(data, broadcast=True)

# ────────────────────────────────────────────────────────────────────────────────
# === 추가된 기능: 1) 검색(Search) ===
# ────────────────────────────────────────────────────────────────────────────────
@app.route('/search')
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    keyword = request.args.get('q', '').strip()
    db = get_db(); cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM product WHERE title LIKE ?",
        (f'%{keyword}%',)
    )
    results = cursor.fetchall()
    return render_template(
        'search.html',
        products=results,
        keyword=keyword
    )

# ────────────────────────────────────────────────────────────────────────────────
# === 추가된 기능: 2) 송금(Transaction) ===
# ────────────────────────────────────────────────────────────────────────────────
@app.route('/transaction', methods=['GET', 'POST'])
def transaction():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    me_id = session['user_id']
    db = get_db(); cursor = db.cursor()
    # 내 정보 불러오기
    cursor.execute("SELECT * FROM user WHERE id = ?", (me_id,))
    me = cursor.fetchone()

    if request.method == 'POST':
        to_id = request.form['to_id']
        amt   = int(request.form['amount'])
        if me['balance'] >= amt:
            tx_id = str(uuid.uuid4())
            # 거래 기록 삽입
            cursor.execute(
                "INSERT INTO transaction "
                "(id, from_id, to_id, amount) VALUES (?, ?, ?, ?)",
                (tx_id, me_id, to_id, amt)
            )
            # 잔액 업데이트
            cursor.execute(
                "UPDATE user SET balance = balance - ? WHERE id = ?",
                (amt, me_id)
            )
            cursor.execute(
                "UPDATE user SET balance = balance + ? WHERE id = ?",
                (amt, to_id)
            )
            db.commit()
            flash('송금 완료!')
        else:
            flash('잔액이 부족합니다.')
        return redirect(url_for('transaction'))

    # GET: 전체 사용자 목록(송금 대상 선택용)
    cursor.execute("SELECT * FROM user WHERE id != ?", (me_id,))
    others = cursor.fetchall()
    return render_template(
        'transaction.html',
        me=me,
        users=others
    )

# ────────────────────────────────────────────────────────────────────────────────
# === 추가된 기능: 3) 관리자 페이지(Admin) ===
# ────────────────────────────────────────────────────────────────────────────────
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT is_admin FROM user WHERE id = ?",
            (session['user_id'],)
        )
        row = cursor.fetchone()
        if not row or row['is_admin'] != 1:
            abort(403)
        return f(*args, **kwargs)
    return decorated

@app.route('/admin/users')
@admin_required
def admin_users():
    db = get_db(); cursor = db.cursor()
    cursor.execute("SELECT * FROM user")
    users = cursor.fetchall()
    return render_template('admin_users.html', users=users)

# ────────────────────────────────────────────────────────────────────────────────
# 앱 실행부: --init-db 옵션으로 테이블 생성, 아니면 서버 실행
# ────────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    if '--init-db' in sys.argv:
        init_db()
        print('>> Database initialized.')
    else:
        socketio.run(app, debug=True)

