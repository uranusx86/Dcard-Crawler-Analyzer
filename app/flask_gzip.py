from flask import after_this_request, request
from cStringIO import StringIO as IO
import gzip
import functools
'''
Usage
@app.route('/')
@gzipped
def gzip_me():
    return "this response has to be gzipped"
'''

minimum_size = 500

def gzipped(f):
    @functools.wraps(f)
    def view_func(*args, **kwargs):
        @after_this_request
        def zipper(response):
            accept_encoding = request.headers.get('Accept-Encoding', '')

            if (response.status_code < 200 or
                response.status_code >= 300 or
                response.direct_passthrough or
                len(response.data) < minimum_size or
                'gzip' not in accept_encoding.lower() or
                'Content-Encoding' in response.headers):
                return response

            gzip_buffer = IO()
            gzip_file = gzip.GzipFile(mode='wb',
                                    compresslevel=6,
                                    fileobj=gzip_buffer)
            gzip_file.write(response.data)
            gzip_file.close()

            response.data = gzip_buffer.getvalue()
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Vary'] = 'Accept-Encoding'
            response.headers['Content-Length'] = len(response.data)

            return response

        return f(*args, **kwargs)
    return view_func
