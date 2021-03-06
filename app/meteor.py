import requests, urllib
import json
import hashlib
import logging, traceback
from datetime import timedelta
from datetime import datetime
from bs4 import BeautifulSoup
from web_app import db
from meteor_db import meteor_articles, meteor_comments  # must under web_app import
from crawler import generators_factory
from crawler import Crawler

class Meteor_crawler(Crawler):
    article_list = []
    headers = { "Content-Type": "application/json;charset=UTF-8" }
    board_name_url = "https://meteor.today/board/get_boards"
    list_url = "https://meteor.today/article/get_new_articles"
    post_html_url = "https://meteor.today/a/"
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

    def __init__(self, req_module):
        super(Meteor_crawler, self).__init__(req_module)
        logging.basicConfig(level=logging.INFO, filename="meteor_crawl.log")

    def response_decode(self, resp):
        return urllib.parse.unquote( resp )   # The data is UTF-8 encoded bytes escaped with URL quoting

    def get_article_list(self, cate, **kw):
        # hot article list
        data = {
                    "boardId": cate,
                    "isCollege": False,
                    "page": 0,
                    "pageSize": 50,
                }

        # get article list in 2 days
        last_article_datetime = datetime.now()
        while (datetime.now() - last_article_datetime).days < 3:
            try:
                res = self.retry_if_fail(self.list_url, retry_num=5, delay_time=5, http_method="post", post_data=data, error_msg="Get article list fail!").json()
                article_list_str = self.response_decode( res["result"] )
                article_list = json.loads(article_list_str)

                for article_info in article_list:
                    yield article_info

                # next fetch
                last_article_datetime = datetime.strptime(article_list[-1]["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
                last_article_datetime = last_article_datetime + timedelta(hours=8)   # UTC to Taipei timezone
                data["page"] += 1
            except Exception as e:
                local_var_key = locals()
                logging.error("=======" + str(datetime.now()) + "=======")
                logging.error(traceback.format_exc())
                logging.error({key: local_var_key[key] for key in local_var_key if key != "article_list" and key != "article_list_str"})
                logging.error("")

    def get_article(self, post_id="", **kw):
        if post_id == "":
            if "list_generator" not in kw:
                print("if provide a NULL post id, must provide a article list")
                return
            for article in kw["list_generator"]:
                try:
                    gender = 0 if article["authorGender"]=='female' else 1
                    yield {"shortId": article["shortId"],
                            "id": article["id"],
                            "authorGender": gender,
                            "authorAlias": article["authorAlias"],
                            "authorSchoolName": article["authorSchoolName"],
                            "createdAt": datetime.strptime(article["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                            "starLength": article["starLength"],
                            "title": article["title"],
                            "content": article["content"]}
                except Exception as e:
                    local_var_key = locals()
                    logging.error("=======" + str(datetime.now()) + "=======")
                    logging.error(traceback.format_exc())
                    logging.error({key: local_var_key[key] for key in local_var_key if key != "kw"})
                    logging.error("")
        else:
            # get a specific article
            pass

    def get_comments(self, post_id="", **kw):
        if post_id == "":
            if "list_generator" not in kw:
                print("if provide a NULL post id, must provide a article list")
                return
            for article in kw["list_generator"]:
                r = self.retry_if_fail(self.post_html_url+article["shortId"], retry_num=5, delay_time=5, error_msg="get article html fail!")
                soup = BeautifulSoup(r.content, 'html.parser')
                #article_content = soup.select('#article_content>p')[0].text

                comments = soup.select('#commentList > .item[data-id|="comment"]')

                if len(comments) == 0:
                    clean_html = soup.prettify()  # clean up the HTML tree
                    soup = BeautifulSoup(clean_html, 'html.parser')
                    #comments = soup.select('#commentList > .item[data-id|="comment"]')
                    comments = soup.select('#commentList > .item')

                cmt_count = db.session.query(meteor_comments.comment_floor).filter_by(art_id=article["id"]).count()

                '''
                if cmt_count is None:
                    cmt_query_begin = 0
                else:
                    cmt_query_begin = cmt_count
                '''

                comments_list = []
                for comt_ind in range(0, len(comments)):
                    try:
                        if len(comments[comt_ind].select('.content')) == 0:
                            continue     # advertisement

                        comment_body = comments[comt_ind].select('.content')[0]

                        nickname_meta = comment_body.select('.header > a')
                        nickname = nickname_meta[0].text.strip('\t\n') if len(nickname_meta) != 0 else comment_body.select('.header')[0].text.strip('\t\n')  # anonymous or deleted

                        avatar = comments[comt_ind].select('.image > img')[0].get('src')
                        avatar = avatar.split("_")[1]
                        if avatar == "1" or avatar == "2" or avatar == "6":
                            gender = 0
                        elif avatar == "3" or avatar == "4" or avatar == "5":
                            gender = 1
                        else:
                            if nickname == "匿名":
                                gender = -1
                            elif nickname == "留言已被刪除":
                                gender = -2
                            else:
                                target_id = nickname_meta[0].get('href').split("/")[-1]
                                r = self.retry_if_fail("https://meteor.today/profile/"+target_id, retry_num=5, delay_time=5, error_msg="get profile fail!")
                                soup = BeautifulSoup(r.content, 'html.parser')
                                script = soup.findAll(lambda tag: tag.name == "script" and "src" not in tag.attrs)
                                gender = 0 if "'female' == 'female'" in script[-1].text else 1

                        meta = comment_body.select('.meta')
                        if len(meta) == 0:   # the comment has been deleted
                            if comment_body.parent.next_sibling is None:
                                next_floor_meta = comment_body.parent.previous_sibling.select('.content > .meta')[0]
                            else:
                                next_floor_meta = comment_body.parent.next_sibling.select('.content > .meta')[0]
                            floor = next_floor_meta.select('a')[0].text[1:] - 1
                            post_time = article["createdAt"]
                        else:
                            meta = meta[0]
                            floor = meta.select('a')[0].text[1:]
                            post_time = meta.select('span')[0].get("ng-bind")
                            post_time = datetime.strptime(post_time.split("'")[1], "%a %b %d %Y %H:%M:%S GMT+0000 (UTC)")

                        likes_btn = comments[comt_ind].select('.mfb > .label')
                        if len(likes_btn) == 0:    # the comment has been deleted
                            likes = 0
                        else:
                            likes_btn = likes_btn[0]
                            likes = likes_btn.text

                        comment = comment_body.select('.description > p')[0].text
                        response = comment_body.select('.description > .tertiary > p')
                        response = response[0].text if len(response) != 0 else ""

                        comments_list.append(
                                {"id": article["id"],
                                "shortId": article["shortId"],
                                "nickname": nickname,
                                "gender": gender,
                                "floor": floor,
                                "post_time": post_time,
                                "likes": likes,
                                "comment": comment,
                                "response": response}
                        )
                    except Exception as e:
                        local_var_key = locals()
                        logging.error("=======" + str(datetime.now()) + "=======")
                        logging.error(traceback.format_exc())
                        logging.error({key: local_var_key[key] for key in local_var_key if key != "comments_list" and key != "comments" and key != "script"})
                        logging.error("")

                if len(comments_list) == 0:
                    continue
                else:
                    yield comments_list
        elif "floor" in kw:
            # specific article specific floor
            pass
        else:
            if not isinstance(post_id, tuple):
                print("meteor article id must contain id and short id")
                return
            # specific article comments

    def save_data(self, article_gen, comt_gen):
        for article in article_gen:
            updated_article = meteor_articles.query.filter_by(art_id=article["id"]).first()
            try:
                if updated_article is None:
                    new_artl = meteor_articles(
                        id = article["id"],
                        shortid = article["shortId"],
                        gender = article["authorGender"],
                        author = article["authorAlias"],
                        school = article["authorSchoolName"],
                        time = article["createdAt"],
                        likes = article["starLength"],
                        title = article["title"],
                        content = article["content"]
                    )
                    db.session.add(new_artl)
                else:
                    # update article
                    article["content"] = self.compare_modify_list(article["content"], updated_article.art_content)
                    updated_article.art_content = article["content"]
            except Exception as e:
                local_var_key = locals()
                logging.error("=======" + str(datetime.now()) + "=======")
                logging.error(traceback.format_exc())
                logging.error({key: local_var_key[key] for key in local_var_key})
                logging.error("")
        db.session.commit()

        for article_cmts in comt_gen: # all comments in the article
            for cmt in article_cmts:
                updated_comt = meteor_comments.query.filter_by(art_id=cmt["id"]).filter_by(comment_floor=cmt["floor"]).first()
                try:
                    if updated_comt is None:      # include has been deleted before fetch
                        new_comt = meteor_comments(
                            id = cmt["id"],
                            shortid = cmt["shortId"],
                            author = cmt["nickname"],
                            gender = cmt["gender"],
                            floor = cmt["floor"],
                            time = cmt["post_time"],
                            likes = cmt["likes"],
                            content = cmt["comment"],
                            response = cmt["response"]
                        )
                        db.session.add(new_comt)
                    else:
                        if cmt["gender"] != -2:      # update except deleted
                            cmt["comment"] = self.compare_modify_list(cmt["comment"], updated_comt.comment_content)
                            updated_comt.comment_content = cmt["comment"]
                            updated_comt.comment_response = cmt["response"]
                except Exception as e:
                    local_var_key = locals()
                    logging.error("=======" + str(datetime.now()) + "=======")
                    logging.error(traceback.format_exc())
                    logging.error({key: local_var_key[key] for key in local_var_key})
                    logging.error("")
            db.session.commit()


crawler = Meteor_crawler(req_module=requests.Session())
article_list_gen = crawler.get_article_list(cate="5800a3b88ef959e188c427e8")
list_gen_factory = generators_factory(article_list_gen)
article_gen = crawler.get_article(list_generator=list_gen_factory())
comt_gen = crawler.get_comments(list_generator=list_gen_factory())
crawler.save_data(article_gen, comt_gen)