[COLOR red]Ru[/COLOR][COLOR green]Tracker[/COLOR] — навигатор по сайту RuTracker.org c возможностью онлайн просмотра (прослушивания) и скачивания контента.
[COLOR orange]Быстрый старт (для новичков):[/COLOR]
Для начала работы нужно ввести свой [COLOR yellow]Логин[/COLOR] и [COLOR yellow]Пароль[/COLOR] на сайте RuTracker.org в настройках в разделе RuTracker. А для просмотра установить в Kodi любые движки из указанных ниже(например - [COLOR pink]TAM[/COLOR]).
[COLOR orange]Поддерживает просмотр через (торрент движки):[/COLOR]
[COLOR gold]Torrserver[/COLOR] при наличии установленной службы [COLOR pink]TorrServer[/COLOR] от [COLOR green]YouROK, Nemiroff[/COLOR].
[COLOR gold]Elementum[/COLOR] при наличии установленного видео дополнения [COLOR pink]Elementum[/COLOR] от [COLOR green]elgatito[/COLOR].
[COLOR gold]Torrent2http[/COLOR] при наличии установленного программного дополнения [COLOR pink]torrent2http[/COLOR] от [COLOR green]anteo, DiMartino, -=Vd=-[/COLOR].
[COLOR gold]TAM[/COLOR] при наличии установленного видео дополнения [COLOR pink]TAM[/COLOR] от [COLOR green]TDW1980[/COLOR].
[COLOR gold]Torrenter[/COLOR] при наличии установленного видео дополнения [COLOR pink]Torrenter[/COLOR] от [COLOR green]inpos[/COLOR].
[COLOR gold]LibTorrent[/COLOR] при наличии установленного программного дополнения [COLOR pink]python-libtorrent[/COLOR] от [COLOR green]DiMartino, srg70, RussakHH, aisman, inpos[/COLOR].
[COLOR gold]TorrentStream[/COLOR] при наличии установленного и настроенного программного дополнения [COLOR pink]AceStream client[/COLOR] от [COLOR green]1orgar[/COLOR].
[COLOR gold]DelugeStream[/COLOR] при наличии установленного программного дополнения [COLOR pink]DelugeStream[/COLOR] от [COLOR green]HAL9000[/COLOR] и установленного торрент-клиента Deluge.
[COLOR red]Не установленные торрент движки не отображаются в дополнении RuTracker (кроме Torrserver'a).[/COLOR]
[COLOR orange]Позволяет скачивать через торрент-клиенты:[/COLOR] [COLOR gold]Transmission[/COLOR] (linux, windows), [COLOR gold]uTorrent[/COLOR] (windows), [COLOR gold]Deluge[/COLOR] (linux, windows), [COLOR gold]qBittorrent[/COLOR] (linux, windows), [COLOR gold]rTorrent[/COLOR] (linux).
Работа дополнения тестировалась только в Kodi 17.6 OSMC(linux armv7l) на железе Raspberry Pi 3b. 
[COLOR red]В других версиях Kodi и системах возможны ошибки, для устранения которых необходим полный лог Kodi с ошибкой.[/COLOR]
Возможен поиск из видео дополнения [COLOR pink]United Search[/COLOR] от [COLOR green]vl.maksime[/COLOR].

Если нужен поиск контента из дополнения [COLOR pink]KinoPoisk[/COLOR] от [COLOR green]TDW1980[/COLOR], то поставьте видео дополнение [COLOR pink]RuTracker Search[/COLOR] от [COLOR green]virserg[/COLOR].

[COLOR orange]Функционал, доступный из контекстного меню:[/COLOR]
[COLOR yellow]$ADDON[plugin.rutracker 40001][/COLOR] — откроется окно с информацией о фильме.
Такое же окно открывается для видеофайлов по которым «прошелся» скрапер.
[COLOR yellow]$ADDON[plugin.rutracker 40002][/COLOR] — просмотр описания раздачи на сайте.
[COLOR yellow]$ADDON[plugin.rutracker 40013][/COLOR] — если контент найден в базе TheMovieDB.org, то вызывается дополнение [COLOR pink]ExtendedInfo Script[/COLOR], в котором отображается информация о фильме (работает только для разделов Фильмы, Сериалы, Мультипликация).
[COLOR yellow]$ADDON[plugin.rutracker 40040][/COLOR] — показывает постер для контента (доступно только в турбо режиме).
[COLOR yellow]$ADDON[plugin.rutracker 40003][/COLOR] — просмотр скринов раздачи с сайта (если эта раздача - видео).
Показывает полноразмерные скрины только с хостингов: imageban.ru, lostpic.net, vfl.ru, funkyimg.com, yapx.ru, postpic4.me, directupload.net, youpicture.org, imgbox.com, ufanet.ru и миниатюры с radikal.ru, fastpic.ru, imagebam.com
В режиме слайд-шоу работают кнопки: стрелка влево(предыдущий скрин), стрелка вправо(следующий скрин), Home(первый скрин), End(последний скрин), ESC(выход), X(выход), Backspace(выход).
[COLOR yellow]$ADDON[plugin.rutracker 40004][/COLOR] — просмотр комментариев к раздаче с сайта. Управление: стрелка вправо (следующий комментарий), стрелка влево (предыдущий комментарий).
[COLOR yellow]$ADDON[plugin.rutracker 40005][/COLOR] — показывает количество раздающих (сидов), качающих (личей), скачиваний и статус раздачи.
[COLOR yellow]$ADDON[plugin.rutracker 30114][/COLOR] — ищет раздачи  в разделе(например Фильмы) после редактирования строки поиска. 
[COLOR yellow]$ADDON[plugin.rutracker 40006][/COLOR] — ищет другие раздачи этого же контента (с другим качеством).
[COLOR yellow]$ADDON[plugin.rutracker 40009][/COLOR] — добавляет контент в раздел "Закладки" (для последующего скачивания и просмотра).
[COLOR yellow]$ADDON[plugin.rutracker 40014][/COLOR] — берет текущие описание и информацию по выбранному контенту с сайтов RuTracker.org и TheMovieDB.org(если в настройках выбран Tmdb).
[COLOR yellow]$ADDON[plugin.rutracker 40018][/COLOR] — переход на страницу по её номеру.
[COLOR yellow]$ADDON[plugin.rutracker 40010][/COLOR] — убирает контент из закладок.
[COLOR yellow]$ADDON[plugin.rutracker 40011][/COLOR] — сразу открывает раздачу из раздела "Закладки".
[COLOR yellow]$ADDON[plugin.rutracker 40030][/COLOR] — запускает кэширование всего содержимого подраздела.
[COLOR yellow]$ADDON[plugin.rutracker 40015][/COLOR] — открывает настройки дополнения.
[COLOR yellow]$ADDON[plugin.rutracker 40035][/COLOR] — удаляет поисковую фразу из раздела "История поиска".
[COLOR yellow]$ADDON[plugin.rutracker 40036][/COLOR] — добавляет контент в Избранное на сайте трекера.
[COLOR yellow]$ADDON[plugin.rutracker 40037][/COLOR] — удаляет контент из раздела Избранное на сайте трекера. 
[COLOR yellow]$ADDON[plugin.rutracker 40038][/COLOR] — ищет поисковую фразу в выбранном разделе из списка.
[COLOR yellow]$ADDON[plugin.rutracker 40041][/COLOR] — добавляет раздачу вместе с описанием в базу TorrServera.

[COLOR orange]Функционал, доступный через настройки дополнения.[/COLOR]
[COLOR brown]На вкладке RuTracker находятся основные настройки:[/COLOR]
[COLOR yellow]$ADDON[plugin.rutracker 50109][/COLOR] — выбор прокси для доступа к сайту.
[COLOR yellow]$ADDON[plugin.rutracker 50107][/COLOR] — доменное имя сайта. Можно поменять на https(http для зоны .lib) зеркало.
[COLOR yellow]$ADDON[plugin.rutracker 50101][/COLOR] — имя пользователя для входа на сайт. 
[COLOR yellow]$ADDON[plugin.rutracker 50102][/COLOR] — пароль для входа. [COLOR red]Логин и пароль обязательны для работы дополнения.[/COLOR]
[COLOR yellow]$ADDON[plugin.rutracker 50160][/COLOR] — жестко задает вид для всех списков раздач. 
[COLOR yellow]$ADDON[plugin.rutracker 50178][/COLOR] — тоже для списка файлов в раздаче.
[COLOR yellow]$ADDON[plugin.rutracker 50145][/COLOR] — позволяет задать один торрент движок для онлайн просмотра(прослушивания) контента или вызов диалога выбора движков.
[COLOR yellow]$ADDON[plugin.rutracker 50179][/COLOR] — показывает ход загрузки данных при открытии страниц.
[COLOR yellow]$ADDON[plugin.rutracker 50122][/COLOR] — выбор источника информации для раздела "Фильмы".
[COLOR yellow]$ADDON[plugin.rutracker 50115][/COLOR] — тоже для раздела "Сериалы".
[COLOR yellow]$ADDON[plugin.rutracker 50130][/COLOR] — и для раздела "Мультипликация".
Эти три настройки позволяют выбирать в качеcтве источника: сайт RuTracker.org(пункт - [COLOR violet]$ADDON[plugin.rutracker 50117][/COLOR]), сайт TheMovieDB.org([COLOR violet]$ADDON[plugin.rutracker 50123][/COLOR]) и только для раздела "Сериалы" сайт TheTVDB.com([COLOR violet]$ADDON[plugin.rutracker 50116][/COLOR]). А также их комбинации([COLOR violet]$ADDON[plugin.rutracker 50124][/COLOR]; [COLOR violet]$ADDON[plugin.rutracker 50125][/COLOR]; [COLOR violet]$ADDON[plugin.rutracker 50126][/COLOR]).
Для отображения рейтинга и трейлера, если они есть, у раздач рекомендуется выставить эти настройки в положение - [COLOR violet]$ADDON[plugin.rutracker 50126][/COLOR].
[COLOR yellow]$ADDON[plugin.rutracker 50135][/COLOR] — очень быстрый режим навигации по сайту(если все предыдущие три настройки установлены так - [COLOR violet]$ADDON[plugin.rutracker 50117][/COLOR])  за счет отключения считывания данных(описания, скриншотов, постеров) по раздачам с трекера. 
[COLOR yellow]$ADDON[plugin.rutracker 50148][/COLOR] — при включенном быстром режиме навигации берутся данные по раздаче только из кэша, если они там есть.
[COLOR yellow]$ADDON[plugin.rutracker 50147][/COLOR] — ищет ссылки скриншотов в описании и помещает их в кэш. Позволяет отключить обработку скриншотов для медленных устройств (ПК).
[COLOR yellow]$ADDON[plugin.rutracker 50140][/COLOR] — выбор способа отображения скринов с трекера.
[COLOR yellow]$ADDON[plugin.rutracker 50105][/COLOR] — рейтинг TMDB (TVDB) в названиях раздач на страницах(если в настройках установлено Tmdb(Tvdb для сериалов)). Только для разделов Фильмы, Сериалы, Мультипликация.
[COLOR yellow]$ADDON[plugin.rutracker 50103][/COLOR] — графическое обозначение статуса у раздач в их названиях.
[COLOR yellow]$ADDON[plugin.rutracker 50136][/COLOR] — количество раздающих(сидов) в названиях раздач.
[COLOR yellow]$ADDON[plugin.rutracker 50106][/COLOR] — отображение обоев(фанарта) для контента в списке раздач.
[COLOR yellow]$ADDON[plugin.rutracker 50146][/COLOR] — отображение картинки(файл fanart.jpg) встроенной в дополнение RuTracker.
[COLOR yellow]$ADDON[plugin.rutracker 50104][/COLOR] — очищает полностью кэш для сайта RuTracker. Кэш используется для ускорения повторного отображения данных на страницах. [COLOR red]При штатной работе дополнения очищать его НЕ требуется.[/COLOR]
[COLOR yellow]$ADDON[plugin.rutracker 50121][/COLOR] — удаляет куки сайта RuTracker. Можно использовать при проблеме со входом на сайт (если логин и пароль введены правильно). 
[COLOR yellow]$ADDON[plugin.rutracker 50108][/COLOR] — при включении при навигации по страницам происходит обновление данных в кэше только у раздач, которые не имели скриншотов в кэше. [COLOR red]Возможно замедление перехода по страницам, особенно в подразделах, где у раздач нет скриншотов. По умолчанию должна быть выключена.[/COLOR] Для чего это нужно догадайтесь сами ;-)  
[COLOR yellow]$ADDON[plugin.rutracker 50180][/COLOR] — выбор качества картинок с сайта lostpic.net(ошибки сайта с оригинальными картинками) 
[COLOR yellow]United Search[/COLOR] — включает поиск для дополнения [COLOR pink]United Search[/COLOR].
[COLOR brown]TM(TV)DB настройки:[/COLOR]
[COLOR yellow]$ADDON[plugin.rutracker 50580][/COLOR] — полностью очищает кэш для сайта TheMovieDB.org, используемый для ускорения повторного отображения информации. [COLOR red]При штатной работе дополнения очищать его НЕ требуется.[/COLOR]
[COLOR yellow]$ADDON[plugin.rutracker 50581][/COLOR] — то же для сайта TheTVDB.com. [COLOR red]При штатной работе дополнения очищать его НЕ требуется.[/COLOR]
[COLOR brown]Настройки на вкладке KinoPoisk больше Не используются.[/COLOR] Они (как и код работы с сайтом Кинопоиск) оставлены до лучших времён. Когда компания Yandex (владелец сайта Кинопоиск) уберет защиту(капчу) от сторонних дополнений или сделает открытый API. Либо найдется Умелец, который сможет поправить работу Кинопоиска в дополнении RuTracker.
[COLOR brown]На вкладке Torrent находятся настройки для торрент-клиентов[/COLOR][COLOR gold] Deluge, qBittorrent, rTorrent[/COLOR],[COLOR gold] uTorrent[/COLOR] и [COLOR gold]Transmission[/COLOR]. 
[COLOR yellow]$ADDON[plugin.rutracker 50301][/COLOR] — позволяет настроить папку по умолчанию(см. ниже) или предлагать каждый раз диалог выбора папки для сохранения файлов раздачи.
[COLOR yellow]$ADDON[plugin.rutracker 50304][/COLOR] — путь к папке для сохранения скаченных файлов в торрент-клиенте. Если оставить пустым, то файлы скачиваются в папку заданную по умолчанию в настройках торрент-клиента.
[COLOR yellow]$ADDON[plugin.rutracker 50304][/COLOR] — ссылка на предыдущую настройку, позволяет ввести путь по буквам.
[COLOR yellow]$ADDON[plugin.rutracker 50305][/COLOR] — если вы отметите этот пункт, то при передаче раздачи в торрент-клиент, будет создана подпапка с наименованием, максимально подходящим для скрапера.
[COLOR yellow]$ADDON[plugin.rutracker 50311][/COLOR] — выбор используемого торрент-клиента.
[COLOR yellow]$ADDON[plugin.rutracker 50312][/COLOR] — ip адрес машины(компьютера и т.п.) где установлен торрент-клиент.
[COLOR yellow]$ADDON[plugin.rutracker 50313][/COLOR] — сетевой порт для связи с торрент-клиентом.
[COLOR yellow]$ADDON[plugin.rutracker 50314][/COLOR] — url для доступа к торрент-клиенту.
[COLOR yellow]$ADDON[plugin.rutracker 50315][/COLOR] — имя пользователя заданное для доступа в торрент-клиенте.
[COLOR yellow]$ADDON[plugin.rutracker 50316][/COLOR] — пароль заданный в торрент-клиенте.
[COLOR brown]В разделе LibTorrent настройки для просмотра через движок libtorrent.[/COLOR]
[COLOR yellow]$ADDON[plugin.rutracker 50412][/COLOR] — [COLOR red]Если вы указываете собственную директорию для буфера, то обязательно указывайте не нужную вам директорию. Так как, после каждого просмотра файлов через LibTorrent, эта директория полностью очищается дополнением. Все файлы в ней удаляются. Если вы не знаете точно для чего вам нужна эта директория, рекомендуется не трогать ее в настройках.[/COLOR]
[COLOR brown]Во вкладке TorrentStream настройки для движка Acestream.[/COLOR]
[COLOR brown]В разделе DelugeStream настройки для этого движка.[/COLOR]
[COLOR brown]На вкладке Torrenter настройки для отображения списка файлов.[/COLOR]
[COLOR brown]Во вкладке Torrent2http настройки для движка torrent2http.[/COLOR]
[COLOR brown]В разделе TAM настройки для просмотра списка файлов.[/COLOR]
[COLOR yellow]$ADDON[plugin.rutracker 50560][/COLOR] — при включении передаёт в дополнение TAM magnet ссылку вместо торрент файла с трекера.
[COLOR brown]Во вкладке Elementum настройки для просмотра списка файлов.[/COLOR]
[COLOR brown]На вкладке TorrServer находятся настройки на службу TorrServer и для отображения списка файлов.[/COLOR]
[COLOR yellow]$ADDON[plugin.rutracker 50550][/COLOR] — позволяет использовать внешнее дополнение от [COLOR green]-=Vd=-[/COLOR] для работы с TorrServer.
[COLOR yellow]$ADDON[plugin.rutracker 50541][/COLOR] — ip адрес машины с работающей службой TorrServer.
[COLOR yellow]$ADDON[plugin.rutracker 50542][/COLOR] — порт для доступа к службе TorrServer.
[COLOR yellow]$ADDON[plugin.rutracker 50551][/COLOR] — включает внешние субтитры при просмотре, если они есть в раздаче.
[COLOR yellow]$ADDON[plugin.rutracker 50552][/COLOR] — если включено, то все проигрываемые раздачи сохраняются в базе программы TorrServer (посмотреть их можно например так [B]http://localhost:8090[/B] ).
[COLOR yellow]$ADDON[plugin.rutracker 50525][/COLOR] — при включении отображается полный путь у файлов раздачи. 
[COLOR yellow]$ADDON[plugin.rutracker 50524][/COLOR] — сортировка по алфавиту файлов раздачи.
[COLOR yellow]$ADDON[plugin.rutracker 50522][/COLOR] — это и так понятно ;-)
[COLOR yellow]$ADDON[plugin.rutracker 50526][/COLOR] — при сортировке учитывается полный путь (папки+файлы) в раздаче.
[COLOR yellow]$ADDON[plugin.rutracker 50527][/COLOR] — отображаются в списке только видео файлы, если включено.
[COLOR yellow]$ADDON[plugin.rutracker 50528][/COLOR] — тоже для аудио файлов. Если включены обе последние настройки, то отображаются в списке только видео и аудио файлы.
