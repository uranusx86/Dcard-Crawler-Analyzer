import logging, traceback
import ast, json
import random
import time
from datetime import timedelta
from datetime import datetime
import cfscrape
from web_app import db
from dcard_db import dcard_articles, dcard_comments   # must under web_app import
from crawler import generators_factory
from crawler import Crawler

class Dcard_crawler(Crawler):
    # convert JS type to Python type
    true = True
    false = False
    null = ""

    proxy = ""   # proxy for request
    cate_url = "https://www.dcard.tw/_api/forums?nsfw=true"
    list_url = "https://www.dcard.tw/_api/forums/{}/posts?popular=false&limit={}"
    article_url = "https://www.dcard.tw/_api/posts/{}"
    comment_url = "https://www.dcard.tw/_api/posts/{}/comments?after={}&limit={}"
    article_list = []

    def __init__(self, req_module):
        super(Dcard_crawler, self).__init__(req_module)
        logging.basicConfig(level=logging.INFO, filename="dcard_crawl.log")

    def response_decode(self, resp):
        #resp.replace("\\u", "\\|u")   # remove emoji
        try:
            # it will parse fail when string contain single quotation (NOT JSON standard)
            return json.loads(resp)
        except Exception as e:
            logging.error("JSON decode error !")
            logging.error(traceback.format_exc())
            logging.error(resp)
            logging.error("")
            try:
                # it only work with string contain strings, bytes, numbers, tuples, lists, dicts, sets, booleans, None, bytes and sets
                # WARNING It is possible to crash the Python interpreter with a sufficiently large/complex string
                # due to stack depth limitations in Python's AST compiler
                return ast.literal_eval(resp)
            except Exception as e1:
                logging.error("AST decode error !")
                logging.error(e1)
                logging.error("")
                return

    def get_article_list(self, cate, **kw):
        '''
        Input:
            cate: board alias, string
            limit: 0 <= N <= 100, integer
            before: the post id of the article, and will skip it and previous articles, integer
        Output:
            JSON list
        '''
        query_api = self.proxy + self.list_url.format(cate, kw['limit'])

        # get article list in 2 days
        last_article_datetime = datetime.now()
        before = 0
        while (datetime.now() - last_article_datetime).days < 3:
            #time.sleep(random.uniform(0.5,1.0))
            try:
                query_url = query_api + ("&before="+str(before) if before != 0 else "")
                article_list_str = self.retry_if_fail(query_url, retry_num=5, delay_time=5, error_msg="Get article list fail! before: {}".format(before))
                article_list = self.response_decode(article_list_str.content.decode("utf-8"))

                for article_info in article_list:
                    yield article_info

                # next fetch
                last_article_datetime = datetime.strptime(article_list[-1]["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
                last_article_datetime = last_article_datetime + timedelta(hours=8)   # UTC to Taipei timezone
                before = article_list[-1]["id"]
            except Exception as e:
                local_var_key = locals()
                logging.error(traceback.format_exc())
                logging.error({key: local_var_key[key] for key in local_var_key if key != "article_list" and key != "article_list_str"})
                logging.error("")

    def get_article(self, post_id="", **kw):
        if post_id == "":
            if "list_generator" not in kw:
                print("if provide a NULL post id, must provide a article list")
                return
            for article in kw["list_generator"]:
                #time.sleep(random.uniform(0.5,1.0))
                query_api = self.proxy + self.article_url.format(article["id"])
                article_encode_str = self.retry_if_fail(query_api, retry_num=5, delay_time=5, error_msg="Get article fail! post id: {}".format(article["id"]))
                article = self.response_decode(article_encode_str.content.decode("utf-8"))

                if "error" in article:
                    logging.info("article may delete, id {}".format( str(article["id"]) ))
                    logging.info(article)
                    continue

                yield article
        else:
            pass
            # get a specific article

    def get_comments(self, post_id="", **kw):
        '''
        Input:
            post_id: id of the article, integer
            limit: 0 <= N <= 100, integer
            after: the comment number you want to skip, integer
        Output:
            JSON list
        '''
        if post_id == "":
            if "list_generator" not in kw:
                print("if provide a NULL post id, must provide a article list")
                return
            for article in kw["list_generator"]:
                cmt_count = db.session.query(dcard_comments.comment_floor).filter_by(art_id=article["id"]).count()

                if cmt_count is None:
                    cmt_query_begin = 0
                else:
                    cmt_query_begin = cmt_count

                # get comment
                comments_list = []
                for comt_ind in range(cmt_query_begin, article["commentCount"], 100):
                    try:
                        #time.sleep(random.uniform(0.5,1.0))
                        query_api = self.proxy + self.comment_url.format(article["id"], comt_ind, kw['limit'])
                        comments_encode_str = self.retry_if_fail(query_api, retry_num=5, delay_time=5, error_msg="Get comment fail! post id: {}, after: {}".format(article["id"], comt_ind))
                        comments = self.response_decode(comments_encode_str.content.decode("utf-8"))
                        if type(comments) is dict and 'error' in comments:
                            continue
                        for a_comment in comments:
                            a_comment["art_anonymousDepartment"] = article["anonymousDepartment"]
                        comments_list.extend(comments)
                    except Exception as e:
                        local_var_key = locals()
                        logging.error(traceback.format_exc())
                        logging.error({key: local_var_key[key] for key in local_var_key if key != "comments_list"})
                        logging.error("")

                if len(comments_list) == 0: # empty list generator wont raise stop iteration exception
                    continue
                else:
                    yield comments_list
        elif "floor" in kw:
            # specific article specific floor
            pass
        else:
            # specific article comments
            pass

    def save_data(self, article_gen, comt_gen):
        for article in article_gen:
            updated_article = dcard_articles.query.filter_by(art_id=article["id"]).first()
            try:
                if updated_article is None:
                    new_artl = dcard_articles(
                                    id = article["id"],
                                    gender = 0 if article["gender"] == 'F' else 1,
                                    owner = 'anonymous' if article["anonymousSchool"] else article["school"] if article["anonymousDepartment"] else article["school"]+article["department"],
                                    time = datetime.strptime(article["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ"),
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
                logging.error(traceback.format_exc())
                logging.error({key: local_var_key[key] for key in local_var_key})
                logging.error("")
        db.session.commit()

        for article_comments in comt_gen:  # all comments in the article
            for comment in article_comments:
                try:
                    # Not delete by self or has been report
                    if not comment["hiddenByAuthor"] and not comment["hidden"]:
                        owner = ('原PO - ' if comment["host"] else '')
                        if comment["anonymous"] and comment["host"]:
                            owner += '匿名'
                        elif comment["anonymous"] or (comment["host"] and comment["art_anonymousDepartment"]):
                            owner += comment["school"]
                        elif comment["school"] is None or comment["department"] is None:
                            owner += '匿名'
                        else:
                            owner += (comment["school"] + comment["department"])
                        new_comt = dcard_comments(
                                    id = comment["postId"],
                                    owner = owner,
                                    gender = 0 if comment["gender"] == 'F' else 1,
                                    floor = comment["floor"],
                                    time = datetime.strptime(comment["updatedAt"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                                    content = comment["content"]
                                )
                    else:
                        new_comt = dcard_comments(
                                    id = comment["postId"],
                                    owner = "這則回應已被本人刪除",
                                    gender = 0,
                                    floor = comment["floor"],
                                    time = datetime.strptime(comment["updatedAt"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                                    content = "已經刪除的內容就像 Dcard 一樣，錯過是無法再相見的！"
                                )
                    db.session.add(new_comt)
                except Exception as e:
                    local_var_key = locals()
                    logging.error(traceback.format_exc())
                    logging.error({key: local_var_key[key] for key in local_var_key if key != "article_comments"})
                    logging.error("")
            db.session.commit()


crawler = Dcard_crawler(req_module=cfscrape.CloudflareScraper())
article_list_gen = crawler.get_article_list(cate="dressup", limit=100)
list_gen_factory = generators_factory(article_list_gen)
article_gen = crawler.get_article(list_generator=list_gen_factory())
comt_gen = crawler.get_comments(list_generator=list_gen_factory(), limit=100)
crawler.save_data(article_gen, comt_gen)