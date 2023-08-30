from flask import Flask
from flask import url_for
from markupsafe import escape

app = Flask(__name__)

@app.route("/")
def hello():
    return '<h1>Hello Totoro!</h1><img src="http://helloflask.com/totoro.gif">'

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