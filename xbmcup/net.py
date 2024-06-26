# -*- coding: utf-8 -*-
# ver 0.4

import os
import sys
import time
import re
import urllib
from urllib.request import build_opener, install_opener, HTTPCookieProcessor, HTTPHandler, HTTPRedirectHandler, BaseHandler, ProxyHandler, ProxyBasicAuthHandler, HTTPError, Request, urlopen
from urllib.parse import urlencode, quote, unquote
from typing import Any, Dict, List, Optional, Tuple
from http.cookiejar import MozillaCookieJar
from http.client import HTTPMessage

# import cookielib  #  перенесено для ускорения интерфейса Kodi в дополнении
# import base64
# import mimetools
# import itertools

try:
    import xbmc, xbmcgui, xbmcvfs   # type: ignore
except ImportError:
    print("* emulate kodi lib *")

    sys.argv[0] = os.path.dirname(__file__).split(os.sep)[-2]

    class xbmcvfs:
        @staticmethod
        def exists(s):
            return os.path.exists(s)

        @staticmethod
        def mkdir(s):
            os.mkdir(s)

        @staticmethod
        def translatePath(p):
            p = p.replace("special:/", os.path.dirname(__file__))
            if not os.path.exists(p):
                os.mkdir(p)
            return p

    class xbmc:
        LOGERROR = 1
        LOGDEBUG = 0

        @staticmethod
        def log(s, d=None):
            print(s)

    class xbmcgui:
        class DialogProgress:
            def __init__(self):
                self._is = False

            def create(self, *argvs):
                pass

            def update(self, *argvs):
                pass

            def iscanceled(self):
                return self._is

            def close(self):
                self._is = True


RE = {
    'content-disposition': re.compile(r'attachment;\sfilename="*([^"\s]+)"|\s')
}

# ################################
#
#   HTTP
#
# ################################


class HTTP:
    def __init__(self):
        self._dirname = xbmcvfs.translatePath('special://temp')
        for subdir in ('xbmcup', sys.argv[0].replace('plugin://', '').replace('/', '')):
            self._dirname = os.path.join(self._dirname, subdir)
            if not xbmcvfs.exists(self._dirname):
                xbmcvfs.mkdir(self._dirname)


    def fetch(self, request, **kwargs):
        self.con, self.fd, self.progress, self.cookies, self.request = None, None, None, None, request

        if not isinstance(self.request, HTTPRequest):
            self.request = HTTPRequest(url=self.request, **kwargs)

        self.response = HTTPResponse(self.request)

        xbmc.log('XBMCup: HTTP: request: ' + str(self.request), xbmc.LOGDEBUG)

        try:
            self._opener()
            self._fetch()
        except Exception as e:
            xbmc.log('XBMCup: HTTP: ' + str(e), xbmc.LOGERROR)
            if isinstance(e, HTTPError):
                self.response.code = e.code
            elif isinstance(e, ImportError): raise
            try:
                 from xbmcup.errors import log
                 log(e, 'http error', msgwarning=True)
            except Exception:
                pass
            self.response.error = e
        else:
            self.response.code = 200

        if self.fd:
            self.fd.close()
            self.fd = None

        if self.con:
            self.con.close()
            self.con = None

        if self.progress:
            self.progress.close()
            self.progress = None

        self.response.time = time.time() - self.response.time

        xbmc.log('XBMCup: HTTP: response: ' + str(self.response), xbmc.LOGDEBUG)

        return self.response


    def _opener(self):

        build: List[BaseHandler] = [HTTPHandler()]

        if self.request.redirect:
            build.append(HTTPRedirectHandler())

        if self.request.proxy_host and self.request.proxy_port:
            if self.request.proxy_protocol == 'socks5':
                import socks
                from sockshandler import SocksiPyHandler
                if self.request.proxy_username:
                        build.append(SocksiPyHandler(socks.PROXY_TYPE_SOCKS5, self.request.proxy_host, self.request.proxy_port, True, self.request.proxy_username, self.request.proxy_password))
                else:
                        build.append(SocksiPyHandler(socks.PROXY_TYPE_SOCKS5, self.request.proxy_host, self.request.proxy_port))
            else:
                build.append(ProxyHandler({self.request.proxy_protocol: self.request.proxy_host + ':' + str(self.request.proxy_port)}))

                if self.request.proxy_username:
                        proxy_auth_handler = ProxyBasicAuthHandler()
                        proxy_auth_handler.add_password('realm', 'uri', self.request.proxy_username, self.request.proxy_password)
                        build.append(proxy_auth_handler)

        if self.request.cookies:
            self.request.cookies = os.path.join(self._dirname, self.request.cookies)
            self.cookies = MozillaCookieJar()
            if os.path.isfile(self.request.cookies):
                self.cookies.load(self.request.cookies)
            build.append(HTTPCookieProcessor(self.cookies))

        install_opener( build_opener(*build) )


    def _fetch(self):
        params = {} if self.request.params is None else self.request.params

        if self.request.upload:
            boundary, upload = self._upload(self.request.upload, params)
            req = Request(self.request.url)
            req.data = upload
        else:

            if self.request.method == 'POST':
                if isinstance(params, dict) or isinstance(params, list):
                    params = urlencode(params).encode()
                req = Request(self.request.url, params)
            else:
                req = Request(self.request.url)

        for key, value in self.request.headers.items():
            req.add_header(key, value)

        if self.request.upload:
            req.add_header('Content-type', 'multipart/form-data; boundary=%s' % boundary)
            req.add_header('Content-length', str(len(upload)))

        if self.request.auth_username and self.request.auth_password:
            import base64 # fast
            auth_str: str = base64.encodebytes(
                f'{self.request.auth_username}:{self.request.auth_password}'.encode()
            ).decode()
            req.add_header('Authorization', 'Basic %s' % auth_str)
                #':'.join([self.request.auth_username, self.request.auth_password])).strip().encode('utf-8'))

        #self.con = urllib2.urlopen(req, timeout=self.request.timeout)
        self.con = urlopen(req)
        # self.response.url = str(self.con.geturl())
        self.response.headers = self._headers( self.con.info() )

        if self.request.download:
            self._download()
        else:
            self.response.body = self.con.read()
            if self.response.headers.get('content-encoding', '') == 'gzip':
                import zlib
                self.response.body = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(self.response.body)

        if self.request.cookies:
            self.cookies.save(self.request.cookies) # type: ignore


    def _download(self):
        if not self.request.download:
            raise

        fd = open(self.request.download, 'wb')
        if self.request.progress:
            self.progress = xbmcgui.DialogProgress()
            self.progress.create(u'Download')

        bs = 1024*8
        size = -1
        read = 0
        name = None

        if self.request.progress:
            if 'content-length' in self.response.headers:
                size = int(self.response.headers['content-length'])
            if 'content-disposition' in self.response.headers:
                r = RE['content-disposition'].search(self.response.headers['content-disposition'])
                if r:
                    name = unquote(r.group(1))

        while 1:
            buf = self.con.read(bs) # type: ignore
            if buf == '':
                break
            read += len(buf)
            fd.write(buf)

            if self.request.progress and self.progress:
                self.progress.update(*self._progress(read, size, name))

        self.response.filename = self.request.download


    def _upload(self, upload, params) -> Tuple[Any, Any]:
        res = []
        from email.generator import Generator # fast
        choose_boundary = Generator._make_boundary  # type: ignore
        boundary = choose_boundary()
        part_boundary = '--' + boundary

        if params:
            for name, value in params.items():
                res.append([part_boundary, 'Content-Disposition: form-data; name="%s"' % name, '', value])

        if isinstance(upload, dict):
            upload = [upload]

        for obj in upload:
            name = obj.get('name')
            filename = obj.get('filename', 'default')
            content_type = obj.get('content-type')
            try:
                body = obj['body'].read()
            except AttributeError:
                body = obj['body']

            if content_type:
                res.append([part_boundary, 'Content-Disposition: file; name="%s"; filename="%s"' % (name, quote(filename)), 'Content-Type: %s' % content_type, '', body])
            else:
                res.append([part_boundary, 'Content-Disposition: file; name="%s"; filename="%s"' % (name, quote(filename)), '', body])

        import itertools # fast
        result = list(itertools.chain(*res))
        result.append('--' + boundary + '--')
        result.append('')
        return boundary, '\r\n'.join(result)


    def _headers(self, raw: HTTPMessage):
        headers = {}
        for tag, value in raw.items():
            if tag and value:
                headers[tag.lower()] = value
        return headers


    def _progress(self, read, size, name):
        res = []
        if size < 0:
            res.append(1)
        else:
            res.append(int( float(read)/(float(size)/100.0) ))
        if name:
            res.append(u'File: ' + name)
        if size != -1:
            res.append(u'Size: ' + self._human(size))
        res.append(u'Load: ' + self._human(read))
        return res

    def _human(self, size):
        human = None
        for h, f in (('KB', 1024), ('MB', 1024*1024), ('GB', 1024*1024*1024), ('TB', 1024*1024*1024*1024)):
            if size/f > 0:
                human = h
                factor = f
            else:
                break
        if human is None:
            return (u'%10.1f %s' % (size, u'byte')).replace(u'.0', u'')
        else:
            return u'%10.2f %s' % (float(size)/float(factor), human)


class HTTPRequest:

    def __init__(
        self,
        url,
        method="GET",
        headers=None,
        cookies=None,
        params=None,
        upload=None,
        download=None,
        progress=False,
        auth_username=None,
        auth_password=None,
        proxy_protocol="http",
        proxy_host=None,
        proxy_port=None,
        proxy_username=None,
        proxy_password="",
        timeout=20.0,
        redirect=True,
        gzip=False,
    ):

        if headers is None:
            headers = {}

        self.url = url
        self.method = method
        self.headers = headers

        self.cookies = cookies

        self.params = params

        self.upload = upload
        self.download = download
        self.progress = progress

        self.auth_username = auth_username
        self.auth_password = auth_password

        self.proxy_protocol = proxy_protocol
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password

        self.timeout = timeout

        self.redirect = redirect

        self.gzip = gzip

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, ','.join('%s=%r' % i for i in self.__dict__.items()))


class HTTPResponse:
    code: Optional[int]
    error: Optional[Exception]
    filename: Optional[str]
    body: Optional[bytes]

    def __init__(self, request):
        self.request = request
        self.code = None
        self.headers = {}
        self.error = None
        self.body = None
        self.filename = None
        self.time = time.time()

    def body_decode(self, encoding: str = 'utf-8', errors: str = "strict"):
        return self.body.decode(encoding, errors) if self.body else ''

    def __repr__(self):
        args = ','.join('%s=%r' % i for i in self.__dict__.items() if i[0] != 'body')
        if self.body:
            args += ',body=<data>'
        else:
            args += ',body=None'
        return '%s(%s)' % (self.__class__.__name__, args)
