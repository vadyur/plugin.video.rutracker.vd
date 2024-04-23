# -*- encoding: utf-8 -*-
import os, sys
from urllib.parse import urljoin
from urllib.request import pathname2url
import xbmc, xbmcgui, xbmcplugin
from xbmcup.errors import log as _log
from xbmcvfs import translatePath

_IS_LIBTORRENT = False
_IS_TORRENTSTREAM = False

file = open


#
#
# Torrent2http
#
#
class Torrent2http:
    def play(self, torrent_file, file_id, DDir=""):
        try:
            sys.path.append(
                os.path.join(
                    translatePath("special://home/"),
                    "addons",
                    "script.module.torrent2http",
                    "lib",
                )
            )
            from torrent2http import State, Engine, MediaType

            progressBar = xbmcgui.DialogProgress()
            from contextlib import closing

            if DDir == "":
                DDir = os.path.join(
                    translatePath("special://temp/"), "xbmcup", "plugin.rutracker"
                )
            progressBar.create("Torrent2Http", "Запуск")
            # XBMC addon handle
            # handle = ...
            # Playable list item
            # listitem = ...
            # We can know file_id of needed video file on this step, if no, we'll try to detect one.
            # file_id = None
            # Flag will set to True when engine is ready to resolve URL to XBMC
            ready = False
            # Set pre-buffer size to 15Mb. This is a size of file that need to be downloaded before we resolve URL to XMBC
            pre_buffer_bytes = 15 * 1024 * 1024

            engine = Engine(
                uri=urljoin("file:", pathname2url(torrent_file)),
                # engine = Engine(uri=magneturi,
                download_path=DDir,
                trackers=[
                    "http://bt.t-ru.org/ann",
                    "http://bt2.t-ru.org/ann",
                    "http://bt3.t-ru.org/ann",
                    "http://bt4.t-ru.org/ann",
                    "http://bt4.t-ru.org/ann?magnet",
                    "http://retracker.mgts.by:80/announce",
                    "udp://opentor.org:2710",
                    "udp://46.148.18.250:2710",
                    "udp://public.popcorn-tracker.org:6969/announce",
                    "udp://tracker.opentrackr.org:1337/announce",
                ],
                connections_limit=None,
                encryption=1,
                enable_upnp=True,
                enable_natpmp=True,
                use_random_port=True,
                listen_port=6881,
                upload_kbps=0,
                dht_routers=[
                    "router.bittorrent.com:6881",
                    "router.utorrent.com:6881",
                    "dht.transmissionbt.com:6881",
                    "router.bitcomet.com:6881",
                ],
                enable_dht=True,
                user_agent="uTorrent/2200(24683)",
            )

            # engine_t2h = engine
            #    self._engine = Engine(uri=urlparse.urljoin('file:', urllib.pathname2url(torrent_file)),
            #                         download_path=self._save_path if self._save_path else self._temp_path,
            #                          connections_limit=None, encryption=1,
            #                         download_kbps=self._dl_speed_limit, upload_kbps=0, keep_complete=keep_files,
            #                         keep_incomplete=keep_files, keep_files=keep_files,
            #                         dht_routers=dht_routers, use_random_port=True, listen_port=6881, user_agent=user_agent,
            #                         resume_file=None if not keep_files else torrent_file + '.resume_data')

            with closing(engine):
                # Start engine and instruct torrent2http to begin download first file,
                # so it can start searching and connecting to peers
                engine.start(file_id)
                progressBar.update(0, "Torrent2Http\nЗагрузка торрента")

                monitor = xbmc.Monitor()
                while not monitor.waitForAbort(0.5) and not ready:

                    status = engine.status()
                    # Check if there is loading torrent error and raise exception
                    engine.check_torrent_error(status)
                    # Trying to detect file_id
                    if file_id is None:
                        # Get torrent files list, filtered by video file type only
                        files = engine.list(media_types=[MediaType.VIDEO])
                        # If torrent metadata is not loaded yet then continue
                        if files is None:
                            continue
                        # Torrent has no video files
                        if not files:
                            break
                            progressBar.close()
                        # Select first matching file
                        file_id = files[0].index
                        file_status = files[0]
                    else:
                        # If we've got file_id already, get file status
                        file_status = engine.file_status(file_id)
                        if progressBar.iscanceled():
                            progressBar.update(0)
                            progressBar.close()
                            break
                        # If torrent metadata is not loaded yet then continue
                        if not file_status:
                            continue
                    if status.state == State.DOWNLOADING:
                        # Wait until minimum pre_buffer_bytes downloaded before we resolve URL to XBMC
                        if file_status.download >= pre_buffer_bytes:
                            ready = True
                            break
                        # print file_status
                        # downloadedSize = status.total_download / 1024 / 1024
                        getDownloadRate = status.download_rate / 1024 * 8
                        # getUploadRate = status.upload_rate / 1024 * 8
                        getSeeds = status.num_seeds

                        line1 = f"Предварительная буферизация: {file_status.download / 1024 / 1024} MB"
                        line2 = "Сиды: " + str(getSeeds)
                        line3 = "Скорость: " + str(getDownloadRate)[:4] + " Mbit/s",
                        progressBar.update(
                            100 * file_status.download / pre_buffer_bytes,
                            f'{line1}\n{line2}\n{line3}'
                        )  #

                    elif status.state in [State.FINISHED, State.SEEDING]:
                        # progressBar.update(0, 'T2Http', 'We have already downloaded file', "")
                        # We have already downloaded file
                        ready = True
                        break

                    if progressBar.iscanceled():
                        progressBar.update(0)
                        progressBar.close()
                        break
                # Here you can update pre-buffer progress dialog, for example.
                # Note that State.CHECKING also need waiting until fully finished, so it better to use resume_file option
                # for engine to avoid CHECKING state if possible.
                # ...
                progressBar.update(0)
                progressBar.close()
                if ready:
                    from t2hxplayer import xPlayer

                    Player = xPlayer(index=file_id, engine=engine)
                    # Resolve URL to XBMC
                    item = xbmcgui.ListItem(path=file_status.url) # type: ignore
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
                    xbmc.sleep(3000)
                    xbmc.sleep(3000)
                    # Wait until playing finished or abort requested
                    while not monitor.waitForAbort(0.5) and xbmc.Player().isPlaying():
                        pass

        except Exception as e:
            _log(e)
