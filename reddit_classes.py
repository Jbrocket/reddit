import re
import os
import requests
from db_manager import Base
from sqlalchemy import Column, Integer, String, Boolean

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String)
    password = Column(String)
    sub_regex = Column(String)
    title_regex = Column(String)
    comment_regex = Column(String)
    sub_num = Column(Integer)
    title_num = Column(Integer)
    comment_num = Column(Integer)
    sub_reverse = Column(Boolean)
    title_reverse = Column(Boolean)
    comment_reverse = Column(Boolean)
    title_attr = Column(String)
    comment_attr = Column(String)

    def __init__(self, sub_regex='.*', title_regex='.*', comment_regex='.*',
                        sub_num=25, title_num=25, comment_num=25,
                        sub_reverse=False, title_reverse=False, comment_reverse=False,
                        title_attr='score', comment_attr='score', user_name='', password=''):

       self.settings = Settings(
           sub_regex, title_regex, 
           comment_regex, sub_num, title_num, comment_num, 
           sub_reverse, title_reverse, comment_reverse, 
           title_attr, comment_attr,
       )
       self.user_name = user_name
       self.password = password
       self.sub_regex = sub_regex if sub_regex else '.*'
       self.title_regex = title_regex if title_regex else '.*'
       self.comment_regex = comment_regex if comment_regex else '.*'
       self.sub_num = sub_num if sub_num else 25
       self.title_num = title_num if title_num else 25
       self.comment_num = comment_num if comment_num else 25
       self.sub_reverse = sub_reverse if sub_reverse else False
       self.title_reverse = title_reverse if title_reverse else False
       self.comment_reverse = comment_reverse if comment_reverse else False
       self.title_attr = title_attr if title_attr else 'score'
       self.comment_attr = comment_attr if comment_attr else 'score'

    def __repr__(self):
        return super().__repr__()

    def init_settings(self):
        self.settings = Settings(
           self.sub_regex, self.title_regex, 
           self.comment_regex, self.sub_num, self.title_num, self.comment_num, 
           self.sub_reverse, self.title_reverse, self.comment_reverse, 
           self.title_attr, self.comment_attr,
       )

class Settings(Base):
    __tablename__ = 'settings'
    user_id = Column(Integer, primary_key=True)
    sub_regex = Column(String)
    title_regex = Column(String)
    comment_regex = Column(String)
    sub_num = Column(Integer)
    title_num = Column(Integer)
    comment_num = Column(Integer)
    sub_reverse = Column(Boolean)
    title_reverse = Column(Boolean)
    comment_reverse = Column(Boolean)
    title_attr = Column(String)
    comment_attr = Column(String)

    def __init__(self, sub_regex='.*', title_regex='.*', comment_regex='.*',
                        sub_num=25, title_num=25, comment_num=25,
                        sub_reverse=False, title_reverse=False, comment_reverse=False,
                        title_attr='score', comment_attr='score'):

       self.sub_regex = sub_regex if sub_regex else '.*'
       self.title_regex = title_regex if title_regex else '.*'
       self.comment_regex = comment_regex if comment_regex else '.*'
       self.sub_num = sub_num if sub_num else 25
       self.title_num = title_num if title_num else 25
       self.comment_num = comment_num if comment_num else 25
       self.sub_reverse = sub_reverse if sub_reverse else False
       self.title_reverse = title_reverse if title_reverse else False
       self.comment_reverse = comment_reverse if comment_reverse else False
       self.title_attr = title_attr if title_attr else 'score'
       self.comment_attr = comment_attr if comment_attr else 'score'

    def __repr__(self):
        return super().__repr__()

class Subreddit(Base):
    __tablename__ = 'subreddits'
    id = Column(Integer, primary_key=True)
    url = Column(String)

    def __init__(self, url: str, user: User): # 2 LOC
        self.url = url
        self.settings = user.settings

    def scrape(self): # 4 LOC
        URL = self.url
        headers  = {'user-agent': 'reddit-{}'.format(os.environ.get('USER', 'cse-30332-sp23'))}
        response = requests.get(URL, headers=headers)
        self.subreddit_posts = response.json()['data']['children']
        
        self.subreddit_posts = sorted(self.subreddit_posts, key=lambda post: post['data'][self.settings.title_attr], reverse=(not self.settings.sub_reverse))

        results = []
        
        option1 = 0
        for post in self.subreddit_posts:
            if len(results) >= self.settings.title_num:
                break
            if self.filter(post):
                results.append(Post(url=f"{self.url[:-5]}/comments/{post['data']['id']}.json", settings=self.settings, data=post))
                option1+=1
        self.subreddit_posts = results
        return self.subreddit_posts

    def display(self, loc: int, titles: bool = False): # 8 LOC
        if not titles:
            return "titles off"
        
        cur = {self.url: loc}
        posts = {}
        results = self.scrape()
        for i, post in enumerate(results):
            posts[post.data['data']['title']] = (i, post.data['data']['selftext'])
        return posts, cur
        
    def filter(self, post): # 3 LOC
        return True if re.findall(pattern=self.settings.title_regex, string=post['data']['title']) else False

    def __repr__(self):
        return super().__repr__()

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    url = Column 

    def __init__(self, url: String, settings: Settings, data): # 6 LOC
        self.url = url
        self.settings = settings
        self.data = data
        self.base_comments = []
        self.title = None
        self.included = set()

    def scrape(self): # 3 LOC
        URL = self.url
        headers  = {'user-agent': 'reddit-{}'.format(os.environ.get('USER', 'cse-30332-sp23'))}
        response = requests.get(URL, headers=headers)
        self.comment_tree = response.json()
        self.title = self.comment_tree[0]['data']['children'][0]['data']['title']
        try:
            self.comment_tree = self.comment_tree[1]['data']['children']
            self.comment_tree = self.comment_tree[:-1]
        except KeyError:
            self.comment_tree = None
            
        try:
            self.comment_tree = sorted(self.comment_tree, key=lambda post: post['data'][self.settings.comment_attr], reverse=(not self.settings.comment_reverse))
        except KeyError:
            print("here")
            pass
        
        
        if not self.comment_tree:
            return "<p>No comments</p>"

        for comment in self.comment_tree:
            if len(self.base_comments) >= self.settings.comment_num:
                break
            if self.filter(comment, True):
                self.base_comments.append(comment)
        return

    def display(self, loc: int, comments: bool = False): # 10 LOC
        string = f"<p>{loc} {self.url}: <br>{self.data['data']['title']} </p>"
        if not comments:
            return string + "<p>comments off</p>"
        
        status = self.scrape()
        if status:
            return string + status
        # return string + self.display_comment_tree(self.base_comments, self.settings.comment_num)
        return self.get_comment_tree(self.base_comments, self.settings.comment_num)
    
    def get_comment_tree(self, comments, num):
        base_comments = []
        global num_comments
        fp = open("data.text", "a+")
        swear_words = ["fuck", "shit", "bitch", "dick", "cunt", "wanker", "pussy", "damn", "ass", "asshole", "bastard", "dickhead", "goddamn", "mufucka"]
        
        def helper(comment: Comment, depth, data):
            global num_comments
            depth = 20
            string = comment.body
            ## get rid of periods
            sentences = re.split('[.!?;:&]', string)
            sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
            for sentence in sentences:
                sentence_lower = sentence.lower()
                for swear_word in swear_words:
                    if re.search(rf'\b{re.escape(swear_word)}\b', sentence_lower) and sentence not in self.included:
                        sentence = re.sub(r'\n+', ', ', sentence)
                        self.included.add(sentence)
                        print(f"{sentence}.")
                        if len(sentence) > 10:
                            fp.write(f"{sentence}.\n")
            
            if depth == num or num_comments >= self.settings.comment_num:
                return True
            
            truth = False
            if data['data']['replies'] != "":
                try:
                    for reply in data['data']['replies']['data']['children']:
                        new_reply = Comment(reply['data']['author'], reply['data']['created_utc'], reply['data']['body'], reply['data'][self.settings.comment_attr])
                        comment.children.append(new_reply)
                        num_comments += 1
                        if helper(new_reply, depth+1, reply) or truth:
                            truth = True
                            break
                except KeyError:
                    pass
            
            return truth
        
        num_comments = 0
        for comment in comments:
            new_comment = Comment(comment['data']['author'], comment['data']['created_utc'], comment['data']['body'], comment['data'][self.settings.comment_attr])
            base_comments.append(new_comment)
            helper(new_comment, 0, comment)
        
        fp.close()
        return base_comments

    def display_comment_tree(self, reply_list: dict, depth: int): # 12 LOC
        global string
        global num_comments
        string = ""
        
        def helper(cur_reply, cur_depth):
            global string
            global num_comments
            
            if cur_depth == depth or num_comments >= self.settings.comment_num:
                return True
            string += "<br>"
            
            truth = False
            try:
                string += self.formatprint(f"<<{cur_reply['data'][self.settings.comment_attr]}>> {cur_reply['data']['body']}", cur_depth)
                num_comments += 1
            except KeyError:
                string += self.formatprint("Comment couldn't be printed", cur_depth)
                pass
            try:
                if cur_reply['data']['replies'] != "":
                    for more_replies in cur_reply['data']['replies']['data']['children']:
                        if helper(more_replies, cur_depth+1) or truth:
                            truth = True
                            break
            except KeyError:
                pass
            return truth
            
        num_comments = 0
        for reply in reply_list:
            string += "<p>-----------------NEW--THREAD-----------------"
            if helper(reply, 0):
                string += "</p>"
                break
            string += "</p>"
            
        return string
    
    def formatprint(self, item, depth):
        total = 0
        spaces = "&nbsp"*4
        add = 50
        string = ""
        
        while total + add < len(item):
            try:
                while item[total + add] != ' ':
                    add += 1
            except IndexError:
                break
            string += f"{depth*spaces}{item[total:total+add]}<br>"
            total += add
            add = 50
        return string + f"{depth*spaces}{item[total:]}<br>"

    def filter(self, item, comments: bool = False): # 6 LOC
        try:
            return True if re.findall(pattern=self.settings.comment_regex, string=item['data']['body']) and comments else False
        except KeyError:
            return False

    def __repr__(self):
        return super().__repr__()
    
class Comment:
    def __init__(self, user, time, body, attr):
        self.children = []
        self.user = user
        self.time = time
        self.body = body
        self.attr = attr