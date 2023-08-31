import os
import click

from flask import Flask
from flask import render_template
from flask import url_for, request, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

from flask_sqlalchemy import SQLAlchemy

from markupsafe import escape

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# 在数据库扩展类实例前加载配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # 关闭对模型修改的监控
app.config['SECRET_KEY'] = 'dev'

db = SQLAlchemy(app) # 实例化数据库扩展

# ----------------------创建数据库模型----------------------
class User(db.Model, UserMixin): # 表名将会是 user（自动生成，小写处理）
    id = db.Column(db.Integer, primary_key=True) # 主键
    name = db.Column(db.String(20)) # 名字
    username = db.Column(db.String(20)) # 用户名
    password_hash = db.Column(db.String(128)) # 密码散列值
    
    def set_password(self, password) -> None:
        self.password_hash = generate_password_hash(password)
        
    def validate_password(self, password) -> bool:
        return check_password_hash(self.password_hash, password)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60)) # 电影标题
    year = db.Column(db.String(4)) # 电影年份

# ---------------创建自定义命令将虚拟数据写入数据库---------------
@app.cli.command()
def forge():
    """Generate fake data."""
    db.create_all()
    
    # 全局的两个变量移动到这个函数内
    name = "jiajianbo"
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]
    
    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)
        
    db.session.commit()
    click.echo('Done.')

# ---------------自定义命令--------------- #
#自定义命令：initdb初始化数据库
@app.cli.command() # 注册为命令，可以传入 name 参数来自定义命令
@click.option('--drop', is_flag=True, help='Create after drop.') # 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop: # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.') # 输出提示信息
    
    
# 自定义命令：创建管理员账号
@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """Create user."""
    db.create_all()

    user = User.query.filter_by(username=username).first() # 查询用户名是否存在
    if user is not None:
        print(user.username)
        click.echo('Updating user...')
        user.username = username
        user.set_password(password) # 设置密码
    else:
        click.echo("Creating user ...")
        user = User(username=username, name='Admin')
        user.set_password(password) # 设置密码
        db.session.add(user)

    db.session.commit()
    click.echo('Done.')

# 模板上下文处理函数
@app.context_processor
def inject_user(): # 函数名可以随便更改
    user = User.query.first()
    return dict(user=user) # 需要返回字典，等同于 return {'user': user}

# 初始化flask-login
login_manager = LoginManager(app) # 实例化扩展类
login_manager.login_view = 'login' # 登录保护，未登录时的请求重定向到登录页

@login_manager.user_loader
def load_user(user_id): # 创建用户加载回调函数，接受用户ID作为参数
    user = User.query.get(int(user_id)) # 用ID作为User模型的主键查询对应的用户
    return user # 返回用户对象
    

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

        user = User.query.filter_by(username=username).first()
        # 验证用户名和密码是否一致
        if username == user.username and user.validate_password(password):
            login_user(user)
            flash('Login success.')
            return redirect(url_for('index')) # 重定向到主页
        
        flash('Invalid username or password.') # 如果验证失败，显示错误信息
        return redirect(url_for('/login')) # 重定向到登录页
    
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
@app.route('/logout')
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
def delete(moive_id):
    movie = Movie.query.get_or_404(moive_id)
    db.session.delete(movie)
    db.session.commit()
    flash("Item deleted.")
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/user/<name>")
def user_page(name):
    return f"User: {escape(name)}" # 使用escape()函数做转义处理，防止XSS攻击

@app.route('/test')
def test_url_for():
    # 下面是一些调用示例
    print(url_for('hello')) # 生成 hello 视图函数对应的 URL，将会输出：/
    # 注意下面两个调用是如何生成包含 URL 变量的 URL 的
    print(url_for('user_page', name='greyli')) # 输出： /user/greyli
    print(url_for('user_page', name='joe')) # 输出： /user/joe
    print(url_for('test_url_for')) # 输出： /test
    # 下面这个调用传入了多余的关键字参数,它会被作为额外的查询字符串添加到 URL 中
    print(url_for('test_url_for', num=2)) # 输出： /test?num=2
    return "Test Page"





    

