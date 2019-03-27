import logging, traceback
import ast, json
import random
import time
from datetime import timedelta
from datetime import datetime
import cfscrape
from web_app import db
from models import dcard_article, dcard_comment

# convert JS type to Python type
true = True
false = False
null = ""

proxy = ""   # proxy for request
cate_url = "https://www.dcard.tw/_api/forums?nsfw=true"
list_url = "https://www.dcard.tw/_api/forums/{}/posts?popular=false&limit={}"
article_url = "https://www.dcard.tw/_api/posts/{}"
comment_url = "https://www.dcard.tw/_api/posts/{}/comments?after={}&limit={}"

logging.basicConfig(level=logging.INFO, filename="crawel.log")

def retry_if_fail(scraper, query_api, retry_num, delay_time, error_msg):
    for _ in range(retry_num):
        try:
            rep = scraper.get( query_api )
            result = rep.content.decode("utf-8")
            if result is not None and result != "":
                break
            logging.error(error_msg)
            logging.error(rep.status_code)
            time.sleep(delay_time)
        except Exception as e:
            logging.error(traceback.format_exc())
    return result

def get_cate(scraper):
    cate = retry_if_fail(scraper, cate_url, retry_num=1, delay_time=0, error_msg="Get category list fail!")
    cate = convert_list_str_to_list(cate)
    cate = [(item["name"],item["alias"]) for item in cate if not item["invisible"]]
    return cate

def get_article_list(scraper, cate="dressup", before=None, limit=30):
    '''
    Input:
        cate: board alias, string
        limit: 0 <= N <= 100, integer
        before: the post id of the article, and will skip it and previous articles, integer
    Output:
        JSON list
    '''
    query_api = proxy + list_url.format(cate, limit)
    query_api = query_api + "&before="+str(before) if before is not None else query_api
    return retry_if_fail(scraper, query_api, retry_num=5, delay_time=5, error_msg="Get article list fail! before: {}".format(before))

def get_article(scraper, post_id):
    '''
    Input:
        post_id: id of the article, integer
    Output:
        JSON object
    '''
    query_api = proxy + article_url.format(post_id)
    return retry_if_fail(scraper, query_api, retry_num=5, delay_time=5, error_msg="Get article fail! post id: {}".format(post_id))

def get_comment(scraper, post_id, after=0, limit=30):
    '''
    Input:
        post_id: id of the article, integer
        limit: 0 <= N <= 100, integer
        after: the comment number you want to skip, integer
    Output:
        JSON list
    '''
    query_api = proxy + comment_url.format(post_id, after, limit)
    return retry_if_fail(scraper, query_api, retry_num=5, delay_time=5, error_msg="Get comment fail! post id: {}, after: {}".format(post_id, after))

def convert_list_str_to_list(list_str):
    #list_str.replace("\\u", "\\|u")   # remove emoji
    try:
        # it will parse fail when string contain single quotation (NOT JSON standard)
        return json.loads(list_str)
    except Exception as e:
        logging.error("JSON decode error !")
        logging.error(e)
        logging.error(traceback.format_exc())
        logging.error(list_str)
        try:
            # it only work with string contain strings, bytes, numbers, tuples, lists, dicts, sets, booleans, None, bytes and sets
            # WARNING It is possible to crash the Python interpreter with a sufficiently large/complex string
            # due to stack depth limitations in Python's AST compiler
            return ast.literal_eval(list_str)
        except Exception as e1:
            logging.error("AST decode error !")
            logging.error(e1)
            return

'''
def str_insert(string, new_string, insert_index):
    return string[:insert_index]+"\n" + \
            ">===================================\n" + \
            new_string+"\n" + \
            "====================================\n" + \
            string[insert_index:]
'''

def compare_modify(content, origin_content):
    content_list = content.split("\n")
    origin_content_list = origin_content.split("\n")

    # if set init with string, return extra char
    # if set init with list, return different elements
    modify_set = set(content_list) - set(origin_content_list)

    if len(modify_set) != 0:
        modify_iter = iter(modify_set)
        line = modify = next(modify_iter)
        base_anchor = anchor = content_list.index( modify )  # assume there is NO duplicate line
        for modify in modify_iter:
            next_anchor = content_list.index( modify )

            # look next element is position-consecutive or not
            # TODO: if find position in origin is 1,0 fail or 1,2,0 fail
            while next_anchor - anchor == 1:
                anchor = next_anchor
                line += ("\n" + modify)
                try:
                    modify = next(modify_iter)
                    next_anchor = content_list.index( modify )
                except StopIteration as e:
                    next_anchor = anchor + 2  # stop loop

            # now, line is a position-consecutive modified string, modify is next position-inconsecutive head
            if base_anchor != 0:
                # find the previous NOT modify
                base_anchor = origin_content_list.index( content_list[base_anchor-1] )
            origin_content_list.insert(base_anchor + 2,
                                        ">===================================\n" +
                                        line+"\n" +
                                        "====================================")

            # new position-consecutive modified string head
            base_anchor = next_anchor
            anchor = next_anchor
            line = modify
    return '\n'.join(origin_content_list)  # list to string

def compare_modify_list(content, origin_content):
    content_list = content.split("\n")
    origin_content_list = origin_content.split("\n")

    base = 0
    modify_filter = 0

    # faster mode
    # b=bytearray("".encode("utf-8"))
    # for i in range(len(a)):
    #   if a[i] - b[i] == 0:
    #       start_ind += 1
    #   else:
    #       break
    # compare start from start_ind

    for i in content_list:
        try:
            modify_filter = origin_content_list.index(i)
            base = 0
        except ValueError as e:
            origin_content_list.insert(modify_filter+base+2,
                                        ">===================================\n" +
                                        i+"\n" +
                                        "====================================")
            base += 1

    return '\n'.join(origin_content_list)  # list to string

if __name__ == '__main__':
    scraper = cfscrape.CloudflareScraper()
    logging.info("===========================")
    logging.info(datetime.now())

    # select cate
    try:
        f = open("cate.txt", "r")
        cate = f.read()
        f.close()
    except Exception:
        cate = ""

    if cate == "":
        f = open("cate.txt", "w")

        cate = get_cate(scraper)
        print("看板列表: ")
        for idx, item in enumerate(cate):
            print(idx, item[0])
        cate_no = int(input("請輸入數字代號："))

        f.write(cate[cate_no][1])
        cate = cate[cate_no][1]
        f.close()

    print("正在爬取 {} 看板...".format(cate))

    # get article list in 2 days
    last_article_datetime = datetime.now()
    article_list = [{"id": None}]
    while (datetime.now() - last_article_datetime).days < 3:
        article_list.extend( convert_list_str_to_list(
            get_article_list(scraper, cate=cate, before=article_list[-1]["id"], limit=100)) )
        last_article_datetime = datetime.strptime(article_list[-1]["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
        last_article_datetime = last_article_datetime + timedelta(hours=8)   # UTC to Taipei timezone

    article_list.pop(0)
    #time.sleep(random.uniform(0.1, 0.3))

    for article_info in article_list:
        query_time = time.time()
        article = convert_list_str_to_list( get_article(scraper, article_info["id"]) )
        if "error" in article:
            logging.info("article may delete, id {}".format( str(article_info["id"]) ))
            logging.info(article)
            continue
        article_origin = dcard_article.query.filter_by(art_id=article_info["id"]).first()

        if article_origin is None:
            # get comment
            comment_list = []
            for comt_ind in range(0, article["commentCount"], 100):
                try:
                    comment_list.extend( convert_list_str_to_list(
                        get_comment(scraper, article_info["id"], after=comt_ind, limit=100)) )
                    #time.sleep(random.uniform(0.1,0.3))
                except Exception as e:
                    logging.error(traceback.format_exc())
                    logging.error(article_info)

            # directly save article
            try:
                new_artl = dcard_article(
                                id = article["id"],
                                gender = 0 if article["gender"] == 'F' else 1,
                                owner = 'anonymous' if article["anonymousSchool"] else article["school"] if article["anonymousDepartment"] else article["school"]+article["department"],
                                time = datetime.strptime(article["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                                title = article["title"],
                                content = article["content"]
                            )
            except Exception as e:
                logging.error(traceback.format_exc())
                logging.error(article)
            db.session.add(new_artl)
            db.session.commit()

            # directly save comment
            for comment in comment_list:
                try:
                    # Not delete by self or has been report
                    if not comment["hiddenByAuthor"] and not comment["hidden"]:
                        owner = ('原PO - ' if comment["host"] else '')
                        if comment["anonymous"] and comment["host"]:
                            owner += '匿名'
                        elif comment["anonymous"] or (comment["host"] and article["anonymousDepartment"]):
                            owner += comment["school"]
                        elif comment["school"] is None or comment["department"] is None:
                            owner += '匿名'
                        else:
                            owner += (comment["school"] + comment["department"])
                        new_comt = dcard_comment(
                                    id = comment["postId"],
                                    owner = owner,
                                    gender = 0 if comment["gender"] == 'F' else 1,
                                    floor = comment["floor"],
                                    time = datetime.strptime(comment["updatedAt"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                                    content = comment["content"]
                                )
                    else:
                        new_comt = dcard_comment(
                                    id = comment["postId"],
                                    owner = "這則回應已被本人刪除",
                                    gender = 0,
                                    floor = comment["floor"],
                                    time = datetime.strptime(comment["updatedAt"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                                    content = "已經刪除的內容就像 Dcard 一樣，錯過是無法再相見的！"
                                )
                    db.session.add(new_comt)
                except Exception as e:
                    logging.error(traceback.format_exc())
                    logging.error(comment)
            db.session.commit()

        else:
            # update article
            try:
                article["content"] = compare_modify_list(article["content"], article_origin.art_content)
                updated_article = dcard_article.query.filter_by( art_id = article_info["id"] ).first()
                updated_article.art_content = article["content"]
            except Exception as e:
                logging.error(traceback.format_exc())
                logging.error(article_info["id"])
                logging.error(article)
                continue

            # update by floor order
            comment_origin_list = dcard_comment.query.filter_by(art_id=article_info["id"]).order_by( dcard_comment.comment_floor.asc() ).all()
            '''
            for idx, comment_origin in enumerate(comment_origin_list):
                if not comment_list[idx]["hiddenByAuthor"] and not comment_list[idx]["hidden"]:
                    try:
                        comment_origin_list[idx].comment_content = compare_modify_list(comment_list[idx]["content"], comment_origin.comment_content)
                    except Exception as e:
                        logging.error(traceback.format_exc())
                        logging.error(comment_list[idx])
            '''
            # get comment
            comment_list = []
            for comt_ind in range(len(comment_origin_list), article["commentCount"], 100):
                try:
                    comment_list.extend( convert_list_str_to_list(
                        get_comment(scraper, article_info["id"], after=comt_ind, limit=100)) )
                    #time.sleep(random.uniform(0.1,0.3))
                except Exception as e:
                    logging.error(traceback.format_exc())
                    logging.error(article_info)
            # add new comment
            for idx in range(len(comment_origin_list), article["commentCount"], 1):
                idx -= len(comment_origin_list)
                try:
                    if not comment_list[idx]["hiddenByAuthor"] and not comment_list[idx]["hidden"]:
                        owner = ('原PO - ' if comment_list[idx]["host"] else '')
                        if comment_list[idx]["anonymous"] and comment_list[idx]["host"]:
                            owner += '匿名'
                        elif comment_list[idx]["anonymous"] or (comment_list[idx]["host"] and article["anonymousDepartment"]):
                            owner += comment_list[idx]["school"]
                        elif comment_list[idx]["school"] is None or comment_list[idx]["department"] is None:
                            owner += '匿名'
                        else:
                            owner += (comment_list[idx]["school"] + comment_list[idx]["department"])
                        new_comt = dcard_comment(
                                    id = comment_list[idx]["postId"],
                                    owner = owner,
                                    gender = 0 if comment_list[idx]["gender"] == 'F' else 1,
                                    floor = comment_list[idx]["floor"],
                                    time = datetime.strptime(comment_list[idx]["updatedAt"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                                    content = comment_list[idx]["content"]
                                )
                    else:
                        new_comt = dcard_comment(
                                    id = comment_list[idx]["postId"],
                                    owner = "這則回應已被本人刪除",
                                    gender = 0,
                                    floor = comment_list[idx]["floor"],
                                    time = datetime.strptime(comment_list[idx]["updatedAt"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                                    content = "已經刪除的內容就像 Dcard 一樣，錯過是無法再相見的！"
                                )
                    db.session.add(new_comt)
                except Exception as e:
                    logging.error(traceback.format_exc())
                    logging.error(comment_list[idx])

            db.session.commit()

        #if time.time() - query_time < 1:
            #time.sleep(1+random.uniform(0.05,0.3)-(time.time() - query_time)) # avoid trigger anti-DDOS

    logging.info(datetime.now())
