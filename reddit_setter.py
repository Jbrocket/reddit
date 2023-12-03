import requests

settings_dict = {
    'sub_regex': '.*',
    "sub_regex": '.*',
    "title_regex": '.*',
    "comment_regex": '.*',
    "sub_num": 100,
    "title_num": 100,
    "comment_num": 100,
    "sub_reverse": False,
    "title_reverse": False,
    "comment_reverse": False,
    "title_attr": 'score',
    "comment_attr": 'score',
}

# use the requests module to make a post request to the reddit API settings endpoint
r = requests.post("http://127.0.0.1:45000/settings/", settings_dict)
print(r.status_code)