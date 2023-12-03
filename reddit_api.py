from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from db_manager import db_session
from reddit_classes import Settings, Subreddit, Post, User
from flask_bootstrap import Bootstrap
# from flaskext.markdown import Markdown
import re
app = Flask(__name__)
bootstrap = Bootstrap(app)
# markdown = Markdown(app)
db_session.expire_on_commit = False

user = None
subs = None

def update_db(user):
    db_session.add(user)
    db_session.commit()
    return

def check_globals(): # 8 LOC
    global user
    global subs

    # create the settings object if it doesn't exist
    if not user:
        user = User()

    # get the subreddit objects from the database and add the settings object
    # if the subreddit objects don't already exist
    if not subs:
        subs = Subreddit.query.all()
        

@app.route('/', methods=["GET", "POST"])
def display_subreddits(): # 6 LOC
    check_globals()
    
    if request.method == "POST":
        user.sub_regex = request.form.get("regex", ".*")
        if user.user_name:
            update_db(user)
    
    sub_list = {}
    num = 0
    for i, sub in enumerate(subs):
        if num >= user.sub_num:
            break
        add = True if re.findall(pattern=user.sub_regex, string=sub.url) else False
        if add:
            sub_list[sub.url] = f"{i}"
            num += 1

    if user.sub_reverse:
        sub_list[::-1]
    return render_template('subreddits.html', subreddit_list=sub_list)

@app.route('/<int:sub_id>/', methods=['GET', 'POST'])
def display_post_titles(sub_id: int): # 2 LOC
    check_globals()
    
    if request.method == "POST":
        user.settings.title_regex = request.form.get("regex", ".*")
        user.title_regex = user.settings.title_regex
        post_dict, cur = Subreddit(subs[sub_id].url, user).display(loc=sub_id, titles=True)
        
        if user.user_name:
            update_db(user)
        return render_template('posts.html', post_list=post_dict, cur=cur)
    else:
        post_dict, cur = Subreddit(subs[sub_id].url, user).display(loc=sub_id, titles=True)
        return render_template('posts.html', post_list=post_dict, cur=cur)


@app.route('/<int:sub_id>/<int:post_id>/', methods=['GET', 'POST'])
def display_post_comments(sub_id: int, post_id: int): # 6 LOC
    check_globals()
    
    if request.method == "POST":
        user.settings.comment_regex = request.form.get("regex", ".*")
        user.comment_regex = user.settings.comment_regex
        
        if user.user_name:
            update_db(user)
        sub = Subreddit(subs[sub_id].url, user)
        
        post = sub.scrape()[post_id]
        comments = post.display(loc=post_id, comments=True)
        
        return render_template('comments.html', parent_comments=comments, title=post.title)
    else:
        sub = Subreddit(subs[sub_id].url, user)
    
        post = sub.scrape()[post_id]
        comments = post.display(loc=post_id, comments=True)
        
        return render_template('comments.html', parent_comments=comments, title=post.title)

@app.route('/settings/', methods=['GET', 'POST'])
def settings(): # 12 LOC
    if request.method == 'POST':
        global user

        user.sub_regex = request.form.get("sub_regex", ".*")
        user.title_regex = request.form.get("title_regex", ".*")
        user.comment_regex = request.form.get("comment_regex", ".*")
        user.sub_num = int(request.form.get("sub_num", 25))
        user.title_num = int(request.form.get("title_num", 25))
        user.comment_num = int(request.form.get("comment_num", 25))
        user.sub_reverse = True if request.form.get("sub_reverse", False) == "True" else False
        user.title_reverse = True if request.form.get("title_reverse", False) == "True" else False
        user.comment_reverse = True if request.form.get("comment_reverse", None) == "True" else False
        user.title_attr = request.form.get("title_attr", 'score')
        user.comment_attr = request.form.get("comment_attr", 'score')
        
        if user.user_name:
            update_db(user)
        return render_template('settings.html', setr=user.settings)
    else:
        check_globals()
        if not user.user_name:
            return redirect(url_for('login'))
        return render_template('settings.html', setr=user.settings)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    check_globals()
    error = ""
    if request.method == 'POST':
        global user
        user_name = request.form.get("user_name", "")
        password = request.form.get("password", "")
        users = User.query.all()
        # for user in users:
        #     print(user.user_name)
        cur: User
        for cur in users:
            if cur.user_name == user_name:
                if cur.password == password:
                    user = cur
                    user.init_settings()
                    error = "user_updated"
                    break
                else:
                    error = "Wrong Password"
                    break
        if not error:
            user = User(user_name=user_name, password=password)
            user.init_settings()
            update_db(user)
        # print(error)
    return render_template('login.html', user=user, error=error)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
    
if __name__=="__main__":
    app.run(host='0.0.0.0', port='9005')
