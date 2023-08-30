import os
import click

from flask import Flask
from flask import render_template
from flask import url_for
from flask_sqlalchemy import SQLAlchemy

from markupsafe import escape


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # 关闭对模型修改的监控
# 在扩展类实例前加载配置
db = SQLAlchemy(app)


# --------创建自定义命令将虚拟数据写入数据库-----------
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

@app.route("/")
def index():
    user = User.query.first() # 读取用户记录
    movies = Movie.query.all() # 读取所有电影记录
    return render_template('index.html', user=user, movies=movies)

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

# -----自定义命令initdb----- #
@app.cli.command() # 注册为命令，可以传入 name 参数来自定义命令
@click.option('--drop', is_flag=True, help='Create after drop.') # 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop: # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.') # 输出提示信息


# -----创建数据库模型----- #
class User(db.Model): # 表名将会是 user（自动生成，小写处理）
    id = db.Column(db.Integer, primary_key=True) # 主键
    name = db.Column(db.String(20)) # 名字
    
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60)) # 电影标题
    year = db.Column(db.String(4)) # 电影年份
    

