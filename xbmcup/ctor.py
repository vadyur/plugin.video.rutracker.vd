# -*- encoding: utf-8 -*-
from typing import Any
import os, re, base64, urllib, json
from .net import HTTP, HTTPRequest
import xmlrpc2scgi
from xmlrpc import client as xmlrpclib
from urllib.parse import quote

# ################################
#
#   TORRENT
#
# ################################

class Torrent:
    def __init__(self, client, **kwargs):
        if client == 'utorrent':
            self.client = UTorrent()

        elif client == 'transmission':
            self.client = Transmission()

        elif client == 'qbittorrent':
            self.client = qBittorrent()

        elif client == 'deluge':
            self.client = Deluge()

        elif client == 'rtorrent':
            self.client = RTorrent()

        self.client.config(login=kwargs.get('login'), password=kwargs.get('password'), host=kwargs.get('host'), port=kwargs.get('port'), url=kwargs.get('url'))

    def list(self):
        return self.client.list()

    def add(self, torrent, dirname):
        return self.client.add(torrent, dirname)

    def delete(self, id):
        return self.client.delete(id)



class UTorrent:
    def config(self, login, password, host, port, url=None):
        self.login = login
        self.password = password

        self.url = 'http://' + host
        if port:
            self.url += ':' + str(port)
        self.url += '/gui/'

        self.http = HTTP()

        self.re = {
            'cookie': re.compile('GUID=([^;]+);'),
            'token': re.compile("<div[^>]+id='token'[^>]*>([^<]+)</div>")
        }



    def list(self):
        obj = self.action('list=1')
        if not obj:
            return None

        res = []
        for r in obj.get('torrents', []):
            res.append({
                'id': r[0],
                'status': self.get_status(r[1], r[4]/10),
                'name': r[2],
                'size': r[3],
                'progress': r[4]/10,
                'download': r[5],
                'upload': r[6],
                'ratio': r[7],
                'upspeed': r[8],
                'downspeed': r[9],
                'eta': r[10],
                'peer': r[12] + r[14],
                'leach': r[12],
                'seed': r[14],
                'add': r[23],
                'finish': r[24],
                'dir': r[26]
            })

        return res


    def add(self, torrent, dirname):
        obj = self.action('action=getsettings')
        if not obj:
            return None

        old_dir = None
        setting = [x[2] for x in obj['settings'] if x[0] == 'dir_active_download']
        if setting:
            old_dir = setting[0]

        if isinstance(dirname, str):
            dirname = dirname.encode('windows-1251')

        obj = self.action('action=setsetting&s=dir_active_download&v=' + quote(dirname, ''))
        if not obj:
            return None

        res = self.action('action=add-file', {'name': 'torrent_file', 'content-type': 'application/x-bittorrent', 'body': torrent})

        if old_dir:
            self.action('action=setsetting&s=dir_active_download&v=' + quote(old_dir.encode('windows-1251'), ''))

        return True if res else None


    def delete(self, id):
        pass

    def action(self, uri, upload=None):
        cookie, token = self.get_token()
        if not cookie:
            return None

        req = HTTPRequest(
            self.url + '?' + uri + '&token=' + token,
            headers={'Cookie': cookie},
            auth_username=self.login,
            auth_password=self.password)

        if upload:
            req.upload = upload

        response = self.http.fetch(req)
        if response.error:
            return None
        else:
            try:
                obj = json.loads(response.body) # type: ignore
            except:
                return None
            else:
                return obj

    def get_token(self):
        response = self.http.fetch(self.url + 'token.html', auth_username=self.login, auth_password=self.password)
        if response.error:
            return None, None

        r = self.re['cookie'].search(response.headers.get('set-cookie', ''))
        if r and response.body:
            cookie = r.group(1).strip()
            r = self.re['token'].search(response.body.decode())
            if r:
                token = r.group(1).strip()
                if cookie and token:
                    return 'GUID=' + cookie, token

        return None, None

    def get_status(self, status, progress):
        mapping = {
            'error':            'stopped',
            'paused':           'stopped',
            'forcepaused':      'stopped',
            'notloaded':        'check_pending',
            'checked':          'checking',
            'queued':           'download_pending',
            'downloading':      'downloading',
            'forcedownloading': 'downloading',
            'finished':         'seed_pending',
            'queuedseed':       'seed_pending',
            'seeding':          'seeding',
            'forceseeding':     'seeding'
        }
        return mapping[self.get_status_raw(status, progress)]


    def get_status_raw(self, status, progress):
        """
            Return status: notloaded, error, checked,
                           paused, forcepaused,
                           queued,
                           downloading,
                           finished, forcedownloading
                           queuedseed, seeding, forceseeding
        """


        started = bool( status & 1 )
        checking = bool( status & 2 )
        start_after_check = bool( status & 4 )
        checked = bool( status & 8 )
        error = bool( status & 16 )
        paused = bool( status & 32 )
        queued = bool( status & 64 )
        loaded = bool( status & 128 )

        if not loaded:
            return 'notloaded'

        if error:
            return 'error'

        if checking:
            return 'checked'

        if paused:
            if queued:
                return 'paused'
            else:
                return 'forcepaused'

        if progress == 100:

            if queued:
                if started:
                    return 'seeding'
                else:
                    return 'queuedseed'

            else:
                if started:
                    return 'forceseeding'
                else:
                    return 'finished'
        else:

            if queued:
                if started:
                    return 'downloading'
                else:
                    return 'queued'

            else:
                if started:
                    return 'forcedownloading'

        return 'stopped'


class Transmission:
    def config(self, login, password, host, port, url):
        self.login = login
        self.password = password

        self.url = 'http://' + host
        if port:
            self.url += ':' + str(port)

        if url[0] != '/':
            url = '/' + url
        if url[-1] != '/':
            url += '/'

        self.url += url

        self.http = HTTP()

        self.token = '0'

    def list(self):
        obj = self.action({'method': 'torrent-get', 'arguments': {'fields': ['id', 'status', 'name', 'totalSize', 'sizeWhenDone', 'leftUntilDone', 'downloadedEver', 'uploadedEver', 'uploadRatio', 'rateUpload', 'rateDownload', 'eta', 'peersConnected', 'peersFrom', 'addedDate', 'doneDate', 'downloadDir', 'peersConnected', 'peersGettingFromUs', 'peersSendingToUs']}})
        if obj is None:
            return None

        res = []
        for r in obj['arguments'].get('torrents', []):
            res.append({
                'id': str(r['id']),
                'status': self.get_status(r['status']),
                'name': r['name'],
                'size': r['totalSize'],
                'progress': 0 if not r['sizeWhenDone'] else int(100.0 * float(r['sizeWhenDone'] - r['leftUntilDone']) / float(r['sizeWhenDone'])),
                'download': r['downloadedEver'],
                'upload': r['uploadedEver'],
                'upspeed': r['rateUpload'],
                'downspeed': r['rateDownload'],
                'ratio': float(r['uploadRatio']),
                'eta': r['eta'],
                'peer': r['peersConnected'],
                'seed': r['peersSendingToUs'],
                'leech': r['peersGettingFromUs'],
                'add': r['addedDate'],
                'finish': r['doneDate'],
                'dir': r['downloadDir']
            })

        return res

    def add(self, torrent, dirname):
        if self.action({'method': 'torrent-add', 'arguments': {'download-dir': dirname, 'metainfo': base64.b64encode(torrent)}}) is None:
            return None
        return True

    def delete(self, id):
        pass

    def action(self, request):
        try:
            jsobj = json.dumps(request)
        except:
            return None
        else:

            while True:
                # пробуем сделать запрос
                if self.login:
                    response = self.http.fetch(self.url+'rpc/', method='POST', params=jsobj, headers={'x-transmission-session-id': self.token}, auth_username=self.login, auth_password=self.password)
                else:
                    response = self.http.fetch(self.url+'rpc/', method='POST', params=jsobj, headers={'x-transmission-session-id': self.token})
                if response.error:

                    # требуется авторизация?
                    if response.code == 401:
                        if not self.get_auth():
                            return None

                    # требуется новый токен?
                    elif response.code == 409:
                        if not self.get_token(response.error):
                            return None

                    else:
                        return None

                else:
                    try:
                        obj = json.loads(response.body) # type: ignore
                    except:
                        return None
                    else:
                        return obj

    def get_auth(self):
        response = self.http.fetch(self.url, auth_username=self.login, auth_password=self.password)
        if response.error:
            if response.code == 409:
                return self.get_token(response.error)
        return False

    def get_token(self, error):
        token = error.headers.get('x-transmission-session-id')
        if not token:
            return False
        self.token = token
        return True

    def get_status(self, code):
        mapping = {
            0: 'stopped',
            1: 'check_pending',
            2: 'checking',
            3: 'download_pending',
            4: 'downloading',
            5: 'seed_pending',
            6: 'seeding'
        }
        return mapping[code]

#
#
class qBittorrent:
    def config(self, login, password, host, port, url):
        self.login = login
        self.password = password

        self.url = 'http://'+host
        if port:
            self.url += ':' + str(port)
        self.url += url

        self.http = HTTP()
        self.cookie = self.get_auth()

    def list(self):
        obj: Any = self.action('/query/torrents')

        if obj is None:
            return None

        res = []
        if len(obj) > 0:
            for r in obj:
                add = {
                    'id': r['hash'],
                    'status': self.get_status(r['state']),
                    'name': r['name'],
                    'size': r['size'],
                    'progress': round(r['progress'], 4)*100,
                    'upspeed': r['upspeed'],
                    'downspeed': r['dlspeed'],
                    'ratio': round(r['ratio'], 2),
                    'eta': r['eta'],
                    'seed': r['num_seeds'],
                    'leech': r['num_leechs'],
                    'dir': r['save_path']
                }
                flist: Any = self.action('/query/propertiesFiles/'+r['hash'])
                if len(flist) > 1: add['dir'] = os.path.join(r['save_path'], r['name'])
                res.append(add)
        return res

    def listdirs(self):
        obj: Any = self.action('/query/preferences')
        if obj is None:
            return None

        try:
            res = [obj['save_path']]
        except:
            res = [None]
        return res, res

    def listfiles(self, id):
        obj: Any = self.action('/query/propertiesFiles/'+id)
        i = -1
        if obj is None:
            return None

        res = []

        if len(obj) == 1:
            strip_path = None
        else:
            tlist: Any = self.list()
            for t in tlist:
                if t['id']==id:
                    strip_path = t['name']
                    break
                strip_path = None

        for x in obj:
            if x['size'] >= 1024 * 1024 * 1024:
                size = str(x['size'] / (1024 * 1024 * 1024)) + 'GB'
            elif x['size'] >= 1024 * 1024:
                size = str(x['size'] / (1024 * 1024)) + 'MB'
            elif x['size'] >= 1024:
                size = str(x['size'] / 1024) + 'KB'
            else:
                size = str(x['size']) + 'B'
            if strip_path:
                path = x['name'].lstrip(strip_path).lstrip('\\')
            else:
                path = x['name']

            if x['priority'] == 0:
                path = path.replace('.unwanted\\','')

            if x.get('progress'):
                percent = int(x['progress'] * 100)
            else:
                percent = 0

            i += 1
            res.append([path.replace('\\','/'), percent, i, size])

        return res

    def get_prio(self, id):
        res = []
        obj: Any = self.action('/query/propertiesFiles/'+id)

        if obj is None:
            return None
        for f in obj:
            res.append(f['priority'])

        return res

    def add(self, torrent, dirname):

        upload={'name': 'torrent_file', 'filename': 'and_nothing_else_matters.torrent',
                           'content-type': 'application/x-bittorrent', 'body': torrent}
        res = self.action('/command/upload', upload=upload)

        if res:
            return True

    def delete(self, id):
        pass

    def add_url(self, torrent, dirname):

        upload={'name': 'urls', 'content-type': 'application/x-bittorrent', 'body': torrent}
        res = self.action('/command/download', upload=upload)

        if res:
            return True

    def setprio(self, id, ind):
        obj: Any = self.action('/query/propertiesFiles/'+id)

        if not obj or ind == None:
            return None

        i = -1
        for x in obj:
            i += 1
            print(str(x))
            if x['priority'] == 1: self.setprio_simple(id, '0', i)

        res = self.setprio_simple(id, '7', ind)

        return True if res else None

    def setprio_simple(self, id, prio, ind):
        if prio == '3': prio = '7'
        params = {'hash':id, 'priority':prio, 'id': ind}
        obj = self.action_post('/command/setFilePrio', params)
        if not obj or ind == None:
            return None

        return True if obj else None

    def setprio_simple_multi(self, menu):
        for hash, action, ind in menu:
            self.setprio_simple(hash, action, ind)

    def action(self, uri, upload=None):
        req = HTTPRequest(self.url + uri, headers={'Cookie': self.cookie})

        if upload:
            req.upload = upload

        response = self.http.fetch(req)

        if response.error:
            return None

        if response.code == 200 and upload:
            return True

        else:
            try:
                obj = json.loads(response.body) # type: ignore
            except:
                return None
            else:
                return obj

    def action_post(self, uri, params=None):
        response = self.http.fetch(self.url + uri, headers={'Cookie': self.cookie},
                                   method='POST', params=params, gzip=True)


        if response.error:
            return None

        if response.code == 200:
            return True

        return response

    def action_simple(self, action, id):
        actions = {'start': ['/command/resume',{'hash':id,}],
                   'stop': ['/command/pause',{'hash':id,}],
                   'remove': ['/command/delete',{'hashes':id}],
                   'removedata': ['/command/deletePerm',{'hashes':id}]}
        obj = self.action_post(actions[action][0],actions[action][1])
        return True if obj else None

    def get_auth(self):
        params = {"username": self.login, "password": self.password}
        response = self.http.fetch(self.url + '/login', method='POST', params=params, gzip=True)
        if response.error:
            return None

        r = re.compile('SID=([^;]+);').search(response.headers.get('set-cookie', ''))
        if r:
            cookie = r.group(1).strip()
            return 'SID=' + cookie

    def get_status(self, code):
        mapping = {
            'error': 'stopped',
            'pausedUP': 'seed_pending',
            'checkingUP': 'checking',
            'checkingDL': 'checking',
            'pausedDL': 'stopped',
            'queuedUP': 'seeding',
            'queuedDL': 'stopped',
            'downloading': 'downloading',
            'stalledDL': 'downloading',
            'uploading': 'seeding',
            'stalledUP': 'seeding',
        }
        if code in mapping:
            return mapping[code]
        else:
            return 'unknown'


class Deluge:
    def config(self, login, password, host, port, url):
        self.login = login
        self.password = password

        self.url = 'http://'+host
        if port:
            self.url += ':' + str(port)
        self.url += url

        self.http = HTTP()

    def get_info(self):
        obj = self.action({"method": "web.update_ui",
                           "params": [[], {}], "id": 1})
        return obj

    def list(self):
        obj = self.get_info()
        if obj is None:
            return None

        res = []
        if len(obj['result'].get('torrents')) > 0:
            for k in obj['result'].get('torrents').keys():
                r = obj['result']['torrents'][k]
                add = {
                    'id': str(k),
                    'status': self.get_status(r['state']),
                    'name': r['name'],
                    'size': r['total_wanted'],
                    'progress': round(r['progress'], 2),
                    'download': r['total_done'],
                    'upload': r['total_uploaded'],
                    'upspeed': r['upload_payload_rate'],
                    'downspeed': r['download_payload_rate'],
                    'ratio': round(r['ratio'], 2),
                    'eta': r['eta'],
                    'peer': r['total_peers'],
                    'seed': r['num_seeds'],
                    'leech': r['num_peers'],
                    'add': r['time_added'],
                    'dir': r['save_path']
                }
                if len(r['files']) > 1: add['dir'] = os.path.join(r['save_path'], r['name'])
                res.append(add)
        return res

    def listdirs(self):
        obj = self.action({"method": "core.get_config", "params": [], "id": 5})
        if obj is None:
            return None

        try:
            res = [obj['result'].get('download_location')]
        except:
            res = [None]
        return res, res

    def listfiles(self, id):
        obj = self.get_info()
        i = 0
        if obj is None:
            return None

        res = []
        obj = obj['result']['torrents'][id]

        if len(obj['files']) == 1:
            strip_path = None
        else:
            strip_path = obj['name']

        for x in obj['files']:
            if x['size'] >= 1024 * 1024 * 1024:
                size = str(x['size'] / (1024 * 1024 * 1024)) + 'GB'
            elif x['size'] >= 1024 * 1024:
                size = str(x['size'] / (1024 * 1024)) + 'MB'
            elif x['size'] >= 1024:
                size = str(x['size'] / 1024) + 'KB'
            else:
                size = str(x['size']) + 'B'
            if strip_path:
                path = x['path'].lstrip(strip_path).lstrip('/')
            else:
                path = x['path']

            if x.get('progress'):
                percent = int(x['progress'] * 100)
            elif obj.get('file_progress') and len(obj['file_progress']) >= i:
                percent = int(obj['file_progress'][i] * 100)
            else:
                percent = 0

            i += 1
            res.append([path, percent, x['index'], size])

        return res

    def get_prio(self, id):
        obj = self.get_info()
        if obj is None:
            return None
        res = obj['result']['torrents'][id]['file_priorities']
        return res

    def add(self, torrent, dirname):
        torrentFile = os.path.join(self.http._dirname, 'deluge.torrent')
        if self.action({'method': 'core.add_torrent_file',
                        'params': [torrentFile,
                                   base64.b64encode(torrent), {"download_path": dirname}], "id": 3}) is None:
            return None
        return True

    def delete(self, id):
        pass

    def add_url(self, torrent, dirname):
        if re.match(r"^magnet\:.+$", torrent):
            if self.action({'method': 'core.add_torrent_magnet', 'params': [torrent,
                                                                            {'download_path': dirname}],
                            "id": 3}) is None:
                return None
        else:
            if self.action({"method": "core.add_torrent_url", "params": [torrent, {'download_path': dirname}],
                            "id": 3}) is None:
                return None
        return True

    def setprio(self, id, ind):
        i = -1
        prios: Any = self.get_prio(id)

        for p in prios:
            i = i + 1
            if p == 1:
                prios.pop(i)
                prios.insert(i, 0)

        prios.pop(int(ind))
        prios.insert(int(ind), 7)

        if self.action({"method": "core.set_torrent_file_priorities", "params": [id, prios], "id": 6}) is None:
            return None

        return True

    def setprio_simple(self, id, prio, ind):
        prios: Any = self.get_prio(id)

        if ind != None:
            prios.pop(int(ind))
            if prio == '3':
                prios.insert(int(ind), 7)
            elif prio == '0':
                prios.insert(int(ind), 0)

        if self.action({"method": "core.set_torrent_file_priorities", "params": [id, prios], "id": 6}) is None:
            return None
        return True

    def setprio_simple_multi(self, menu):
        id = menu[0][0]
        prios: Any = self.get_prio(id)

        for hash, action, ind in menu:
            prios.pop(int(ind))
            if action == '3':
                prios.insert(int(ind), 7)
            elif action == '0':
                prios.insert(int(ind), 0)

        if self.action({"method": "core.set_torrent_file_priorities", "params": [id, prios], "id": 6}) is None:
            return None

    def action(self, request):
        cookie = self.get_auth()
        if not cookie:
            return None

        try:
            jsobj = json.dumps(request)
        except:
            return None
        else:
            response = self.http.fetch(self.url + '/json', method='POST', params=jsobj,
                                       headers={'X-Requested-With': 'XMLHttpRequest', 'Cookie': cookie,
                                                'Content-Type': 'application/json; charset=UTF-8'})

            if response.error:
                return None

            else:
                try:
                    obj = json.loads(response.body) # type: ignore
                except:
                    return None
                else:
                    return obj

    def action_simple(self, action, id):
        actions = {'start': {"method": "core.resume_torrent", "params": [[id]], "id": 4},
                   'stop': {"method": "core.pause_torrent", "params": [[id]], "id": 4},
                   'remove': {"method": "core.remove_torrent", "params": [id, False], "id": 4},
                   'removedata': {"method": "core.remove_torrent", "params": [id, True], "id": 4}}
        obj = self.action(actions[action])
        return True if obj else None

    def get_auth(self):
        params = json.dumps({"method": "auth.login", "params": [self.password], "id": 0})
        response = self.http.fetch(self.url + '/json', method='POST', params=params, gzip=True,
                                   headers={'X-Requested-With': 'XMLHttpRequest',
                                            'Content-Type': 'application/json; charset=UTF-8'})
        if response.error:
            return None

        auth = json.loads(response.body) # type: ignore
        if auth["result"] == False:
            return False
        else:
            r = re.compile('_session_id=([^;]+);').search(response.headers.get('set-cookie', ''))
            if r:
                cookie = r.group(1).strip()
                return '_session_id=' + cookie

    def get_status(self, code):
        mapping = {
            'Queued': 'stopped',
            'Error': 'stopped',
            'Checking': 'checking',
            'Paused': 'seed_pending',
            'Downloading': 'downloading',
            'Active': 'seed_pending',
            'Seeding': 'seeding'
        }
        return mapping[code]



class RTorrent:
    def config(self, login, password, host, port, url):
        self.url = 'scgi://'+host
        if port:
            self.url += ':' + str(port)
        self.rtc = xmlrpc2scgi.RTorrentXMLRPCClient(self.url)

    def version(self):
        return self.rtc.system.client_version()

    def list(self):
        pass

    def add(self, torrent, dirname):
        if str(self.rtc.load_raw_start(xmlrpclib.Binary(torrent))) == '0':
                return True
        return False

    def add_file(self, torrent_file):
        if str(self.rtc.load_start(torrent_file)) == '0':
                return True
        return False

    def delete(self, id):
        pass

