import requests, urllib
import json
import logging, traceback
from datetime import timedelta
from datetime import datetime
from bs4 import BeautifulSoup
import abc
from web_app import db
from meteor_db import meteor_articles, meteor_comments  # must under web_app import

board_name_url = "https://meteor.today/board/get_boards"
content_url = "https://meteor.today/article/get_basic_article_content_short/"
'''
header: {"Content-Type": "application/json;charset=UTF-8"}
{
    "shortId": "cdyeNu"  # article url
}
'''
content_url_ = "https://meteor.today/article/get_basic_article_content/"
'''
header: {"Content-Type": "application/json;charset=UTF-8"}
{
    "articleId": "5cb9c2bcb4b260b95f8e35c9"
}
'''

# hot article list
headers = { "Content-Type": "application/json;charset=UTF-8" }
data = {
            "boardId": "56fcf952299e4a3376892c1f",
            "isCollege": False,
            "page": 0,
            "pageSize": 30,
        }
r = requests.post("https://meteor.today/article/get_hot_articles", headers=headers, json=data)
article_list_str = urllib.parse.unquote( r.json()["result"] )  # The data is UTF-8 encoded bytes escaped with URL quoting
article_list = json.loads(article_list_str)

for article in article_list:
    print("="*30)
    print(article["shortId"])

    r = requests.get("https://meteor.today/a/"+article["shortId"])
    soup = BeautifulSoup(r.content, 'html.parser')
    article_content = soup.select('#article_content>p')[0].text

    print(article["createdAt"])

    new_artl = meteor_articles(
                    id = article["id"],
                    shortid = article["shortId"],
                    gender = 0 if article["authorGender"] == 'female' else 1,
                    author = article["authorAlias"],
                    school = article["authorSchoolName"],
                    time = datetime.strptime(article["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                    likes = article["starLength"],
                    title = article["title"],
                    content = article["content"]
                )
    db.session.add(new_artl)
    db.session.commit()

    comments = soup.select('#commentList > .item[data-id|="comment"]')
    #comments = soup.select('#commentList')
    #comments = comments.findAll(lambda tag: "data-id" in tag.attrs) # another method

    if len(comments) == 0:
        clean_html = soup.prettify()  # clean up the HTML tree
        soup = BeautifulSoup(clean_html, 'html.parser')
        comments = soup.select('#commentList > .item[data-id|="comment"]')

    for comment in comments:
        try:
            comment_body = comment.select('.content')[0]

            nickname_meta = comment_body.select('.header > a')
            nickname = nickname_meta[0].text.strip('\t\n') if len(nickname_meta) != 0 else comment_body.select('.header')[0].text.strip('\t\n')  # 匿名

            avatar = comment.select('.image > img')[0].get('src')
            avatar = avatar.split("_")[1]
            if avatar == "1" or avatar == "2" or avatar == "6":
                gender = 0
            elif avatar == "3" or avatar == "4" or avatar == "5":
                gender = 1
            else:
                if nickname == "匿名":
                    gender = -1
                else:
                    data = {
                            targetId: nickname_meta[0].get('href').split("/")[-1],
                            page: 0
                        }
                    r = requests.post("https://meteor.today/user/get_follow_single_user", json=data)
                    gender = 0 if r.json()["author"]["gender"] == "female" else 1

            meta = comment_body.select('.meta')[0]
            floor = meta.select('a')[0].text[1:]
            post_time = meta.select('span')[0].get("ng-bind")

            likes_btn = comment.select('.mfb > .label')[0]
            likes = likes_btn.text

            comment = comment_body.select('.description > p')[0].text
            response = comment_body.select('.description > .tertiary > p')
            response = response[0].text if len(response) != 0 else ""
            print("-"*40)
            print(floor)
            print(datetime.strptime(post_time.split("'")[1], "%a %b %d %Y %H:%M:%S GMT+0000 (UTC)"))
            print(nickname)
            print(likes)
            print(comment)
            print(response)
            print("-"*40)

            new_comt = meteor_comments(
                            id = article["id"],
                            shortid = article["shortId"],
                            author = nickname,
                            gender = gender,
                            floor = floor,
                            time = datetime.strptime(post_time.split("'")[1], "%a %b %d %Y %H:%M:%S GMT+0000 (UTC)"),
                            likes = likes,
                            content = comment,
                            response = response
                        )
            db.session.add(new_comt)

        except Exception as e:
            print(traceback.format_exc())
            print(comment)

    db.session.commit()
