from datetime import datetime
from itsdangerous import URLSafeTimedSerializer as Serializer
from flaskblog import db, login_manager, app
from flask_login import UserMixin

# 登入管理器，用於加載用戶
@login_manager.user_loader
def load_user(user_id):
    # 根據用戶 ID 從資料庫中獲取用戶實例
    return User.query.get(int(user_id))

# 用戶定義
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True) # 唯一的用戶 ID
    username = db.Column(db.String(20), unique=True, nullable=False) # 唯一的用戶名
    email = db.Column(db.String(120), unique=True, nullable=False) # 唯一的電子郵件
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')  # 頭像文件名稱
    password = db.Column(db.String(60), nullable=False) # 密碼
    posts = db.relationship('Post', backref='author', lazy=True) # 與貼文的關聯關係

    # 生成密碼重設令牌
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec) # 創建序列化器，設定過期時間
        return s.dumps({'user_id': self.id}).decode('utf-8') # 將用戶 ID 編碼為令牌

    # 驗證密碼重設令牌
    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY']) # 創建序列化器
        try:
            user_id = s.loads(token)['user_id'] # 嘗試解碼令牌以獲取用戶 ID
        except:
            return None # 如果令牌無效或過期，返回 None
        return User.query.get(user_id) # 根據用戶 ID 從資料庫中獲取用戶

    # 定義打印用戶時的輸出格式
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

# 貼文定義
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True) # 唯一的貼文 ID
    title = db.Column(db.String(100), nullable=False) # 貼文標題
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) # 貼文日期
    content = db.Column(db.Text, nullable=False) # 貼文內容
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # 外鍵，對應貼文作者

    # 定義打印貼文時的輸出格式
    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"