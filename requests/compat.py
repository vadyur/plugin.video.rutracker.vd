# -*- coding: utf-8 -*-

"""
pythoncompat
"""

from .packages import chardet

import sys

# -------
# Pythons
# -------

# Syntax sugar.
_ver = sys.version_info

#: Python 2.x?
is_py2 = (_ver[0] == 2)

#: Python 3.x?
is_py3 = (_ver[0] == 3)

import json

# ---------
# Specifics
# ---------

from urllib.parse import urlparse, urlunparse, urljoin, urlsplit, urlencode, quote, unquote, quote_plus, unquote_plus, urldefrag
from urllib.request import parse_http_list, getproxies, proxy_bypass
from http import cookiejar as cookielib
from http.cookies import Morsel
from io import StringIO
from collections import OrderedDict

builtin_str = str
str = str
bytes = bytes
basestring = (str, bytes)
numeric_types = (int, float)
