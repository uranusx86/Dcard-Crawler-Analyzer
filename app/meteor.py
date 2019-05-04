import requests, urllib
import json
import logging, traceback
from bs4 import BeautifulSoup

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

    #comments = soup.select('#commentList > .item')
    comments = soup.findAll(lambda tag: "data-id" in tag.attrs) # remove ads

    if len(comments) == 0:
        clean_html = soup.prettify()  # clean up the HTML tree
        soup = BeautifulSoup(clean_html, 'html.parser')
        comments = soup.select('#commentList > .item')

    for comment in comments:
        try:
            avatar = comment.select('.image > img')[0].get('src')

            comment_body = comment.select('.content')[0]

            nickname = comment_body.select('.header > a')
            nickname = nickname[0].text.strip('\t\n') if len(nickname) != 0 else comment_body.select('.header')[0].text.strip('\t\n')  # 匿名

            meta = comment_body.select('.meta')[0]
            floor = meta.select('a')[0].text
            post_time = meta.select('span')[0].get("ng-bind")

            comment = comment_body.select('.description > p')[0].text
            response = comment_body.select('.description > .tertiary > p')
            response = response[0].text if len(response) != 0 else ""
            print("-"*40)
            print(floor)
            print(nickname)
            print(comment)
            print(response)
            print("-"*40)
        except Exception as e:
            print(traceback.format_exc())
            print(comment)
