import abc
import collections
import requests
import logging

class Crawler(metaclass=abc.ABCMeta):  # Abstract base class
    def __init__(self, req_module=requests):
        self.req = req_module

    def retry_if_fail(self, query_api, retry_num, delay_time, error_msg):
        for _ in range(retry_num):
            try:
                resp = self.req.get( query_api )
                result = resp.content.decode("utf-8")
                if result is not None and result != "":
                    break
                logging.error(error_msg)
                logging.error(resp.status_code)
                time.sleep(delay_time)
            except Exception as e:
                logging.error(traceback.format_exc())
        return result

    '''
    def str_insert(string, new_string, insert_index):
        return string[:insert_index]+"\n" + \
                ">===================================\n" + \
                new_string+"\n" + \
                "====================================\n" + \
                string[insert_index:]
    '''

    def compare_modify(self, content, origin_content):
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

    def compare_modify_list(self, content, origin_content):
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

    @abc.abstractmethod
    def response_decode(self):
        return NotImplemented()

    @abc.abstractmethod
    def get_article_list(self, cate, **kw):
        return NotImplemented()

    @abc.abstractmethod
    def get_article(self, post_id="", **kw):
        return NotImplemented()

    @abc.abstractmethod
    def get_comments(self, post_id="", **kw):
        return NotImplemented()

# https://stackoverflow.com/a/55762535
def generators_factory(iterable):
    it = iter(iterable)
    deques = []
    already_gone = []

    def new_generator():
        new_deque = collections.deque()
        new_deque.extend(already_gone)
        deques.append(new_deque)

        def gen(mydeque):
            while True:
                if not mydeque:             # when the local deque is empty
                    newval = next(it)       # fetch a new value and
                    already_gone.append(newval)
                    for d in deques:        # load it to all the deques
                        d.append(newval)
                yield mydeque.popleft()

        return gen(new_deque)

    return new_generator