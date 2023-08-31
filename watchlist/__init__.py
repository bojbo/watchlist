import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


app = Flask(__name__)

# 在数据库扩展类实例前加载配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # 关闭对模型修改的监控
app.config['SECRET_KEY'] = 'dev'

db = SQLAlchemy(app) # 实例化数据库扩展
# 初始化flask-login
login_manager = LoginManager(app) # 实例化扩展类
login_manager.login_view = 'login' # 登录保护，未登录时的请求重定向到登录页

@login_manager.user_loader
def load_user(user_id): # 创建用户加载回调函数，接受用户ID作为参数
    from watchlist.models import User
    user = User.query.get(int(user_id)) # 用ID作为User模型的主键查询对应的用户
    return user # 返回用户对象

# 模板上下文处理函数
@app.context_processor
def inject_user(): # 函数名可以随便更改
    from watchlist.models import User
    user = User.query.first()
    return dict(user=user) # 需要返回字典，等同于 return {'user': user}

from watchlist import views, errors, commands