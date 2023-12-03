import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base

#create an engine for your DB using sqlite and storing it in a file named reddit.sqlite

engine = create_engine('sqlite:///test.sqlite')
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False))

Base = declarative_base()
Base.query = db_session.query_property()

def init_db(): # 15 LOC

    # import your classes that represent tables in the DB and then create_all of the tables
    from reddit_classes import Settings, Subreddit, Post, User
    Base.metadata.create_all(bind=engine, checkfirst=True)
    user = User()
    subreddit_list = list()
    count = 0
    with open('sub_info.csv', newline='') as csvfile:
        subreddits = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in subreddits:
            if row[2] == "nsfw=false":
                subreddit_list.append(Subreddit(f"https://www.reddit.com/r/{row[1]}.json", user))
                count += 1
            if count >= 1000:
                break
    
    # read in the subreddit lists from the given CSV and add the first 1000 SFW subreddits to your database by creating Subreddit objects
    

    # save the database
    for subreddit in subreddit_list:
        db_session.add(subreddit)
    db_session.commit()
