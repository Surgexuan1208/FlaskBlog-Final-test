import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail

# 初始化
app = Flask(__name__) 
# 配置應用程式的密鑰
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245' 
# 配置資料庫的路徑
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'site.db')
# 初始化資料庫
db = SQLAlchemy(app)
# 密碼的加密與驗證
bcrypt = Bcrypt(app)
# 初始化用戶登錄管理器
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
# 配置郵件伺服器
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
# 啟用傳輸層安全性 (TLS)
app.config['MAIL_USE_TLS'] = True
# 從環境變數中提取電子郵件帳戶資訊，用於安全性（避免硬編碼）
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
# 初始化郵件
mail = Mail(app)

# 從 flaskblog 導入路由
from flaskblog import routes
