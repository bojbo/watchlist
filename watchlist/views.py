from watchlist import app, db
from watchlist.models import Movie, User
import logging

from flask import request,redirect, url_for, flash, render_template
from flask_login import login_user, current_user, login_required,logout_user

from markupsafe import escape

logger = logging.getLogger('werkzeug')
# handler = logging.FileHandler('test.log')
# logger.addHandler(handler)

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not current_user.is_authenticated: # 如果当前用户未登录
            return redirect(url_for('index')) # 重定向到主页
        # 获取表单数据
        title = request.form.get('title')
        year = request.form.get('year')
        # 验证数据
        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input.') # 显示错误提示
            return redirect(url_for('index')) # 重定向到主页
        # 保存表单数据到数据库
        movie = Movie(title=title, year=year) # 创建记录
        db.session.add(movie) # 添加到数据库会话
        db.session.commit() # 提交数据库会话
        flash('Item created.') # 显示成功创建的提示
        return redirect(url_for('index')) # 重定向到主页
    
    movies = Movie.query.all()
    return render_template('index.html', movies=movies)

# 用户登录
@app.route('/login', methods=['GET', "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash("Invalid input.")
            return redirect(url_for('login'))

        user = User.query.first()
        # 验证用户名和密码是否一致
        if username == user.username and user.validate_password(password):
            login_user(user)
            flash('Login success.')
            return redirect(url_for('index')) # 重定向到主页
        
        flash('Invalid username or password.') # 如果验证失败，显示错误信息
        return redirect(url_for('login')) # 重定向到登录页
    
    return render_template('login.html')

# 支持设置用户名称 User Column: user
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']

        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))
        
        current_user.name = name
        # current_user 会返回当前登录用户的数据库记录对象
        # 等同于下面的语法
        # user = User.query.filter_by(name=name).first()
        # user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))
    
    return render_template('settings.html')


# 用户登出
@app.route('/logout', methods=['POST'])
@login_required # 用于视图保护
def logout():
    logout_user()
    flash('Goodbye.')
    return redirect(url_for('index')) # 登出后重定向到首页


# 编辑电影条目
@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == 'POST':
        title = request.form['title']
        year = request.form['year']

        if not title or not year or len(year) != 4 or len(title) > 60:
            flash("Invalid input.")
            return redirect(url_for('edit', movie_id = movie_id)) # 重定向回对应的编辑页面
        
        movie.title = title
        movie.year = year
        db.session.commit()
        flash('Item updated.')
        return redirect(url_for('index'))
    
    return render_template('edit.html', movie=movie)

# 删除电影条目
@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash("Item deleted.")
    return redirect(url_for('index'))

@app.route("/user/<name>")
def user_page(name):
    return f"User: {escape(name)}" # 使用escape()函数做转义处理，防止XSS攻击