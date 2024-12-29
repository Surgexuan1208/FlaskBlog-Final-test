import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt, mail
from flaskblog.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                             PostForm, RequestResetForm, ResetPasswordForm)
from flaskblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

# 首頁
@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)  # 獲取當前頁碼，預設為第 1 頁
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)# 分頁顯示每頁 5 篇貼文
    return render_template('home.html', posts=posts) # 渲染主頁模板

# 關於頁面
@app.route("/about")
def about():
    return render_template('about.html', title='About')

# 註冊
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:  # 如果用戶已登入，回到主頁
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8') # 加密密碼
        user = User(username=form.username.data, email=form.email.data, password=hashed_password) # 創建新用戶
        db.session.add(user) # 新增用戶到資料庫
        db.session.commit() # 提交變更
        flash('Your account has been created! You are now able to log in', 'success') # 提示註冊成功
        return redirect(url_for('login')) # 重定回到登入頁面
    return render_template('register.html', title='Register', form=form)

# 登入
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: # 如果用戶已登入，回到主頁
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        # 按電子郵件查找用戶
        user = User.query.filter_by(email=form.email.data).first()
        # 驗證密碼
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data) # 登入用戶
            next_page = request.args.get('next') 
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger') # 提示失敗消息
    return render_template('login.html', title='Login', form=form)

# 登出
@app.route("/logout")
def logout():
    logout_user() 
    return redirect(url_for('home')) # 回到主頁

# 保存圖片
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn) # 設置保存路徑

    output_size = (125, 125) # 設置尺寸
    i = Image.open(form_picture) # 打開
    i.thumbnail(output_size) # 縮放
    i.save(picture_path) # 保存

    return picture_fn # 返回圖片名稱

# 帳戶管理
@app.route("/account", methods=['GET', 'POST'])
@login_required # 需要登入
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data: # 如果提交了圖片，保存並更新
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data # 更新用戶名
        current_user.email = form.email.data # 更新電子郵件
        db.session.commit() 
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username 
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file) # 獲取頭像路徑
    return render_template('account.html', title='Account',image_file=image_file, form=form)

# 新增貼文
@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post(): 
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user) # 創建貼文
        db.session.add(post) # 加入資料庫
        db.session.commit() # 提交變更
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',form=form, legend='New Post')

# 查看貼文
@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id) # 查找貼文，找不到返回 404
    return render_template('post.html', title=post.title, post=post)

# 更新貼文
@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id) # 查找貼文
    if post.author != current_user: 
        abort(403) # 如果不是，返回 403 錯誤
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data # 更新標題
        post.content = form.content.data # 更新內容
        db.session.commit() 
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',form=form, legend='Update Post')

# 刪除貼文
@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post) # 刪除
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

# 用戶貼文
@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int) # 獲取當前頁碼
    user = User.query.filter_by(username=username).first_or_404() # 查找用戶
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5) # 按日期降序排列並分頁顯示
    return render_template('user_posts.html', posts=posts, user=user)

# 發送重設密碼郵件
def send_reset_email(user):
    token = user.get_reset_token() # 獲取重設令牌
    msg = Message('Password Reset Request',sender='noreply@demo.com',recipients=[user.email]) # 設置郵件內容
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg) # 發送郵件

# 密碼重設請求
@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first() # 查找用戶
        send_reset_email(user) # 發送重設密碼郵件
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login')) # 回到登入頁面
    return render_template('reset_request.html', title='Reset Password', form=form)

# 密碼重設
@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token) # 驗證令牌
    if user is None:
        flash('That is an invalid or expired token', 'warning') # 提示錯誤消息
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8') # 加密的新密碼
        user.password = hashed_password # 更新密碼
        db.session.commit() # 提交變更
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)
