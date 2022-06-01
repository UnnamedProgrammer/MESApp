from kivymd.app import MDApp
from kivy.lang.builder import Builder
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
#================================Интерфейс====================================
from widgets.screenmanager import MESScreenManager
from widgets.screens import MainWindow, SecondWindow, MainScreen, LoadingWindow, IdleWindow, EnteredWeightWindow, ShiftTaskWindow
from widgets import RV, ContentNavigationDrawer, TpaCard
from widgets.graph.DetailGraph import DetailGraph
from kivymd.uix.picker import MDDatePicker
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.spinner import MDSpinner
from kivy.metrics import dp
from kivy.core.window import Window
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.boxlayout import MDBoxLayout
#=============================================================================
from _thread import *
from kivy.clock import mainthread
import time
import socket
import pickle
from datetime import date, datetime, timedelta
import struct
from kivy.config import Config
import logging as log

Config.set('kivy', 'exit_on_escape', '0')

Builder.load_file("kv/mes.kv")


class MES(MDApp):
    def __init__(self, **kwargs):
        log.info("Инициализация класса приложения")
        super(MES, self).__init__(**kwargs)
        self.samples = 100
        self.rvdata = []
        self.Screen = MainScreen.MainScreen()
        self.data = b""
        self.sock = None
        self.serverhost = '192.168.118.68'
        self.serverport = 9090
        self.connection_attempt = 0
        self.connected = False
        self.nowscreenname = ""
        self.date_dialog = MDDatePicker(
            primary_color=get_color_from_hex("#6699CC"))
        self.tpaReaderIds = None
        self.dialog = None
        self.loaddialog = None
        Window.bind(on_keyboard=self.ReturnToMain)
        self.buffer = b""
        #Данные в окне графика
        self.TakeProductsPlanForTpaDetail = ""
        self.TakeProductFact = ""
        self.cyclenorm = ""
        self.averagecycle = ""
        self.weightnorm = ""
        self.previousShiftdateCount = 0
        self.enddate = None
        self.startdate = None
        self.escapebuttoncreated = False
        self.installedPressForms = {}

    def get_color(self, hex):
        log.info("Задействована функция get_color")
        return get_color_from_hex(hex)

    def build(self):
        log.info("Построение макета приложения")
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "BlueGray"
        # Задаём расписание запрашивая обновление списка ТПА каждые 120 сек
        Clock.schedule_interval(self.SendUpdateTpaCards, 120)
        return self.Screen

    def on_exit(self):
        log.info("Выход из приложения")
        self.sock.send(pickle.dumps('exit'))

    # Метод обработки подключения к серверу
    def connection(self):
        self.change_window("LoadingWindow")
        log.info("Переключен на экран загрузки")
        while True and self.connection_attempt <= 100:
            log.info("Начат процесс подключения")
            try:
                self.root.ids.toolbar.title = "Ожидание сервера..."
                if(self.connected == False):
                    log.info("Подключение к серверу: " +
                             str(self.serverhost) + ":" + str(self.serverport))
                    self.root.ids.load_spin.active = True
                    self.root.ids.load_status_hint.text = 'Подключение...'
                    self.sock = socket.socket(
                        socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.connect((self.serverhost, self.serverport))
                    self.sock.setblocking(0)
                    self.connected = True
                    log.info("Подключение успешно")
                    self.sock.send(pickle.dumps("16011500"))
                    break
            except socket.error as e:
                log.info(
                    "Подключение не удалось, отсчет до повторного подключения")
                self.root.ids.toolbar.title = "Подключение..."
                seconds = 5
                secondsendlist = ['секунду.', 'секунды.', 'секунд.']
                end = ""
                self.root.ids.load_spin.active = False
                while seconds > 0:
                    if seconds == 5:
                        end = secondsendlist[2]
                    if seconds >= 2 and seconds <=4:
                        end = secondsendlist[1]
                    if seconds == 1:
                        end = secondsendlist[0]
                    self.root.ids.load_status_hint.text = 'Попытка переподключения к серверу через ' + \
                        str(seconds) + ' ' + end
                    time.sleep(1)
                    seconds -= 1
                self.connection_attempt += 1
        if(self.connected == False):
            self.root.ids.load_spin.active = False
            self.root.ids.load_status_hint.text = 'Подключение неудачно, нет ответа от сервера.'
        else:
            #======================Обработка подключения===========================
            # Получаем данные от сервера
            self.root.ids.load_spin.active = True
            self.root.ids.load_status_hint.text = 'Получение данных с сервера...'
            while self.connected:
                time.sleep(0.1)
                if(self.connected == False):
                    log.info("Отключение от сервера")
                    self.change_window('LoadingWindow')
                    self.root.ids.load_spin.active = False
                    self.root.ids.load_status_hint.text = "Сервер выключен"
                    time.sleep(3)
                    self.connection_attempt = 0
                    self.sock.close()
                    self.on_start()
                    break
                DeserializeData = None
                try:
                    #Получаем размер данных принимая 4 байта
                    data = b""
                    buffer = b""
                    try:
                        packetsize = self.sock.recv(4)
                    except socket.error as e:
                        if(e.strerror == "Удаленный хост принудительно разорвал существующее подключение" or
                                e.strerror == "Connection reset by peer"):
                            self.connected = False
                            raise socket.error
                        else:
                            continue

                    if packetsize != b"":
                        try:
                            size = struct.unpack("I", packetsize)
                            #Получаем данные исходя из их размеров
                            if (size[0] >= 4096):
                                while True:
                                    try:
                                        log.info("Получаю данные от сервера")
                                        data = self.sock.recv(size[0])
                                        if not data:
                                            break
                                        buffer += data
                                    except:
                                        break
                                data = buffer
                            else:
                                log.info("Получаю данные от сервера")
                                data = self.sock.recv(size[0])
                            lendata = len(data)
                            sizepack = struct.pack("I", lendata)
                            size = struct.unpack("I", sizepack)
                            log.info(
                                f"Получено: {str(round(size[0]/1024,2))}Кб данных")
                            try:
                                DeserializeData = pickle.loads(data)
                                log.info("Данные распакованы")
                            except:
                                if(self.connected != False):
                                    self.ShowAlert(
                                        "Не получилось распаковать данные, попробуйте еще.")
                                    log.warning("Ошибка при распаковке данных")
                                else:
                                    pass
                        except socket.error as e:
                            pass
                    if isinstance(DeserializeData, dict):
                        # Получаем список ТПА при первом подключении
                        if list(DeserializeData.keys())[0] == 'TpaListFromServer':
                            log.info(
                                "Данные после распаковки -> 'TpaListFromServer'")
                            TpaList = DeserializeData['TpaListFromServer']

                            self.PutTpaUpdate(TpaList)
                            self.change_window("MainWindow")
                            self.root.ids.toolbar.title = "Информация по ТПА"
                            continue

                        #Получение списка ТПА и соответствующих им Oid считывателей
                        if(list(DeserializeData.keys())[0]) == "TpaReaderList":
                            log.info(
                                "Данные после распаковки -> 'TpaReaderList'")
                            self.tpaReaderIds = DeserializeData["TpaReaderList"]
                            continue

                        # Получаем обновлённый список ТПА после запроса к серверу
                        if list(DeserializeData.keys())[0] == 'UpdateTpaListFromServer':
                            log.info(
                                "Данные после распаковки -> 'UpdateTpaListFromServer'")
                            UpdatedTpaList = DeserializeData['UpdateTpaListFromServer']
                            self.PutTpaUpdate(UpdatedTpaList)
                            continue

                        #Получение данных для вывода графика, статистики, простоев и распоряжений
                        if list(DeserializeData.keys())[0] == 'TpaDatePoints':
                            log.info(
                                "Данные после распаковки -> 'TpaDatePoints'")
                            if (DeserializeData["TpaDatePoints"] == []):
                                self.addGraphFromServer(DeserializeData)
                            else:
                                self.addGraphFromServer(DeserializeData)
                            IdleQuery = {}
                            try:
                                IdleQuery['NeedTpaIdle'] = self.tpaReaderIds[self.root.ids.toolbar.title]
                                self.sock.send(pickle.dumps(IdleQuery))
                            except KeyError:
                                if (self.nowscreenname == "MainWindow"):
                                    continue
                                if (self.nowscreenname == "SecondWindow"):
                                    IdleQuery['NeedTpaIdle'] = self.tpaReaderIds[self.root.ids.toolbar.title]
                                    self.sock.send(pickle.dumps(IdleQuery))
                            continue

                        # Получение данных для графика за прошлую смену
                        if list(DeserializeData.keys())[0] == 'HistoryDatePoints':
                            log.info(
                                "Данные после распаковки -> 'HistoryDatePoints'")
                            if (DeserializeData["HistoryDatePoints"] == []):
                                self.loaddialog.dismiss()
                            else:
                                try:
                                    self.AddHistoryGraphFromServer(DeserializeData,
                                                                   DeserializeData["Plan"][self.root.ids.toolbar.title]["plan"])
                                    if (self.escapebuttoncreated == False):
                                        self.AddEscapeGraphButton()
                                        self.escapebuttoncreated = True
                                    self.sock.send(self.buffer)
                                    self.buffer = b""
                                except KeyError:
                                    self.AddHistoryGraphFromServer(DeserializeData,
                                                                   300)
                                    self.sock.send(self.buffer)
                                    self.buffer = b""
                            continue

                        # При возниконвении ошибок с SQL
                        if list(DeserializeData.keys())[0] == 'SQLError':
                            log.info("Данные после распаковки -> 'SQLError'")
                            self.root.ids.load_spin.active = False
                            self.root.ids.load_status_hint.text = DeserializeData["SQLError"]
                            continue

                        # Получение списка простоев, введенного веса, и распоряжений
                        if list(DeserializeData.keys())[0] == 'TpaIdleList':
                            log.info(
                                "Данные после распаковки -> 'TpaIdleList'")
                            self.LoadIdle(DeserializeData)
                            self.LoadEnteredWeight(DeserializeData)
                            self.LoadShiftTask(DeserializeData)
                            self.loaddialog.dismiss()
                            if(self.root.ids.manager.current != "SecondWindow"):
                                self.change_window("SecondWindow")
                            continue

                except socket.error as error:
                    self.change_window('LoadingWindow')
                    self.root.ids.load_spin.active = False
                    if(error.strerror == None):
                        self.root.ids.load_status_hint.text = "Сервер выключен."
                    else:
                        self.root.ids.load_status_hint.text = error.strerror
                    time.sleep(3)
                    self.connection_attempt = 0
                    self.connected = False
                    self.sock.close()
                    self.on_start()
                    break

    def on_start(self):
        # Запуск потока обработки сокета
        start_new_thread(self.connection, ())
        self.root.ids.date_pick.text = "Дата: " + str(date.today())
        log.info("Запущен основной поток обработки сервера")

    # Метод вызываемый из потока self.connection в основном потоке для смены экрана
    @mainthread
    def change_window(self, name):
        log.info(f"Смена экрана на {name}")
        self.root.ids.manager.current = name

    # Метод вызываемый при закрытии программы
    def on_stop(self):
        try:
            self.sock.send(pickle.dumps('exit'))
            log.info("Отправлено сообщение об отключении")
        except:
            pass
        self.connected = False
        return super().on_stop()

    def on_pause(self):
        try:
            log.info("Отправлено сообщение об отключении")
            self.sock.send(pickle.dumps('exit'))
        except:
            pass
        self.connected = False
        return super().on_pause()

    # Метод вызываемый из потока self.PutTpaUpdate в основном потоке
    # для обновления представления списка ТПА
    def LoadingCards(self, tpas):
        '''Метод обработки данных для виджета RecycleView полученных с сервера'''
        log.info("Загрузка полученных с сервера карточек ТПА")
        card_color = (0, 0, 0, 1)
        LEamColor = (0, 0, 0, 1)
        LMesColor = (0, 0, 0, 1)
        self.rvdata = []

        for tpa in tpas:
            # Устанавливается цвет карточки
            if (tpas[tpa][1] == "В работе" and tpas[tpa][2] == "В работе"):
                card_color = (0.91, 0.99, 0.95, 1)
            if ((tpas[tpa][1] == "В работе" and tpas[tpa][2] == "В простое") or
                    (tpas[tpa][1] == "В простое" and tpas[tpa][2] == "В работе")):
                card_color = (0.99, 0.84, 0.84, 1)
            if (tpas[tpa][1] == "В простое" and tpas[tpa][2] == "В простое"):
                card_color = (0.08, 0.63, 0.71, 1)
            # Устанавливается цвет техсостояний
            if (tpas[tpa][2] == "В работе"):
                LEamColor = "00BD39"
            else:
                LEamColor = "FB000D"
            if (tpas[tpa][1] == "В работе"):
                LMesColor = "00BD39"
            else:
                LMesColor = "FB000D"
            #Инициализируем список карточек
            self.rvdata.append({'name': tpas[tpa][0],
                                'techstateEam': "[color=" + LMesColor + "]" + tpas[tpa][1]+"[/color]",
                                'techstateTerminal': "[color=" + LEamColor + "]" + tpas[tpa][2]+"[/color]",
                                'md_bg_color': card_color,
                                'installedPf': tpas[tpa][3],
                                'productsPlan': tpas[tpa][4],
                                'products': tpas[tpa][5],
                                'cyclenorm': tpas[tpa][6],
                                'weightnorm': str(float(tpas[tpa][7])),
                                'averagecycle': tpas[tpa][8]
                                })
            self.installedPressForms[tpas[tpa][0]] = tpas[tpa][3]
        self.ApplyTpaUpdate()

    #Метод запускающий поток обновления карточек
    @mainthread
    def PutTpaUpdate(self, UpdatedTpaList):
        log.info("Запуск потока обработки карточек ТПА")
        start_new_thread(self.LoadingCards, (UpdatedTpaList,))

    # Метод вызываемый из потока self.connection в основном потоке
    # для отправки запроса на сервер для обновления списка ТПА
    @mainthread
    def SendUpdateTpaCards(self, dt):
        try:
            self.sock.send(pickle.dumps('NeedUpdate'))
            log.info("Отправлено сообщение о требовании обновления списка ТПА")
        except:
            pass

    #Метод применения изменений списка ТПА полученного с сервера
    @mainthread
    def ApplyTpaUpdate(self):
        self.root.ids.container.data = self.rvdata
        self.root.ids.container.refresh_from_data()
        log.info("Обновление карточек ТПА")

    #Метод возвращающий на главный экран
    def ReturnToMain2(self):
        log.info("Возвращение на главный экран")
        self.root.ids.manager.current = "MainWindow"
        self.root.ids.toolbar.title = "Информация по ТПА"
        self.root.ids.nav_drawer.set_state("close")
        self.enddate = None
        self.startdate = None
        self.root.ids.date_pick.text = "Дата: " + str(date.today())

    #Метод открывающий навбар
    def NavDrawTrigger(self):
        log.info("Навбар открыт")
        self.root.ids.nav_drawer.set_state("open")

    #Метод для окраски chip на экране детализации
    def changeDetailColor(self, text):
        log.info("Окрашивание чипов")
        if int(text) < 0:
            return self.get_color("#dc3545")
        else:
            return self.get_color("#28a745")

    #Метод загрузки экрана детализации при нажатии на карточку ТПА
    def SelectDetailScreen(self, instance, productsplan, productfact, cyclenorm, averagecycle, weightnorm):
        log.info("Запуск инициализации окна детализации")
        self.Show_loaddialog()
        self.loaddialog.open()
        getdetail = {}
        self.TakeProductsPlanForTpaDetail = productsplan
        self.TakeProductFact = productfact
        self.cyclenorm = cyclenorm
        self.averagecycle = averagecycle
        self.weightnorm = weightnorm
        getdetail["NeedTpaDatePoints"] = self.tpaReaderIds[instance]
        DataToServer = pickle.dumps(getdetail)
        try:
            self.sock.send(DataToServer)
            log.info("Отправлены данные о требовании получить точки графика")
        except:
            pass
        self.root.ids.toolbar.title = instance
        self.root.ids.escape.opacity = 0
        self.root.ids.escape.disabled = True
        self.previousShiftdateCount = 0

    #Метод вызываемый в self.connection для загрузки графика
    #на основе полученных данных сервера
    @mainthread
    def addGraphFromServer(self, datepoints):
        log.info("Рисование графика")
        self.root.ids.plan.text = str(self.TakeProductsPlanForTpaDetail)
        self.root.ids.fact.text = str(self.TakeProductFact)
        self.root.ids.cyclenorm.text = str(self.cyclenorm)
        self.root.ids.averagecycle.text = str(self.averagecycle)
        self.root.ids.weightnorm.text = str(self.weightnorm)
        self.root.ids.detailgraph.clear_widgets()
        self.root.ids.detailgraph.LoadGraph(
            datepoints, self.TakeProductsPlanForTpaDetail, self.TakeProductFact, self.installedPressForms[self.root.ids.toolbar.title])
        self.root.ids.diffprod.text = str(self.root.ids.detailgraph.diff)
        self.root.ids.endtime.text = self.root.ids.detailgraph.TimeToEndPlan
        log.info("График отрисован")

    def SendQueryForGraphHistory(self):
        log.info("Отправка сообщения для получения истории смен на графике")
        self.Show_loaddialog()
        self.loaddialog.open()
        data = {}
        self.previousShiftdateCount += 1
        nowdate = datetime.now()
        startdate = None
        if(nowdate.hour >= 7 and nowdate.hour <= 19):
            startdate = datetime(datetime.now().year,
                                 datetime.now().month,
                                 datetime.now().day,
                                 7)
        else:
            startdate = datetime(datetime.now().year,
                                 datetime.now().month,
                                 datetime.now().day,
                                 7)
        enddate = startdate - timedelta(hours=12*self.previousShiftdateCount)

        if(self.previousShiftdateCount > 1):
            startdate = enddate + timedelta(hours=12)

        data = {"NeedGraphHistoryPoint": {"StartDate": enddate,
                                          "EndDate": startdate,
                                          "ReaderOid": self.tpaReaderIds[self.root.ids.toolbar.title]}}

        dataidles = {"NeedHistoryIdles": {"StartDate": enddate,
                                          "EndDate": startdate,
                                          "ReaderOid": self.tpaReaderIds[self.root.ids.toolbar.title]}}
        try:
            packingData = pickle.dumps(data)
            self.sock.send(packingData)

            packingData = pickle.dumps(dataidles)
            self.buffer = packingData
        except socket.error as e:
            self.loaddialog.dismiss()
            self.ShowAlert(e.strerror)
            return
        self.enddate = startdate
        self.startdate = enddate
        self.root.ids.escape.opacity = 1
        self.root.ids.escape.disabled = False
        log.info("Запрос на информацию о предыдущей смене отправлен")

    @mainthread
    def AddHistoryGraphFromServer(self, points, plan):
        log.info("Вывод графика за прошлую смену")
        self.root.ids.detailgraph.LoadGraphHistory(
            self.enddate, self.startdate, points, plan, self.installedPressForms[self.root.ids.toolbar.title])
        self.root.ids.date_pick.text = "Дата: " + str(self.startdate)

    #Метод вывода информации об ошибке
    @mainthread
    def ShowAlert(self, errstr):
        self.dialog = MDDialog(
            title="ОШИБКА",
            text=errstr,
            radius=[20, 7, 20, 7],
            buttons=[
                MDRaisedButton(
                    text="Закрыть", text_color=(1, 1, 1, 1), on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.open()

    #Отоброжение процесса загрузки детализации по ТПА
    def Show_loaddialog(self):
        self.loaddialog = MDDialog()
        self.loaddialog.add_widget(MDSpinner(
            size_hint=(None, None),
            pos_hint={'center_x': .5, 'center_y': .5},
            active=True,
            size=(dp(32), dp(32))))

    def ReturnToMain(self, window, key, *largs):
        if (key == 27):
            if(self.root.ids.manager.current == "SecondWindow"):
                self.change_window("MainWindow")
                self.enddate = None
                self.startdate = None
                self.root.ids.date_pick.text = "Дата: " + str(date.today())
            if(self.root.ids.manager.current == "idleWindow"):
               self.change_window("SecondWindow")
            if(self.root.ids.manager.current == "EnteredWeightWindow"):
                self.change_window("SecondWindow")
            if(self.root.ids.manager.current == "ShiftTaskWindow"):
                self.change_window("SecondWindow")

    @mainthread
    def AddEscapeGraphButton(self):
        self.root.ids.escape.opacity = 1
        self.root.ids.escape.disabled = False

    def GetEscapeGraph(self):
        self.Show_loaddialog()
        self.loaddialog.open()
        self.previousShiftdateCount = 0
        getdetail = {}
        getdetail["NeedTpaDatePoints"] = self.tpaReaderIds[self.root.ids.toolbar.title]
        DataToServer = pickle.dumps(getdetail)
        self.sock.send(DataToServer)
        self.root.ids.date_pick.text = "Дата: " + str(date.today())
        self.root.ids.escape.opacity = 0
        self.root.ids.escape.disabled = True

    @mainthread
    def LoadIdle(self, IdleListFromServer):
        log.info("Загрузка простоев")
        idlecount = 0
        tablerowdata = []
        end = ""
        for idle in list(IdleListFromServer['TpaIdleList'].keys()):
            idlecount += 1
            if(IdleListFromServer['TpaIdleList'][idle]['end'] == None):
                pass
            else:
                end = IdleListFromServer['TpaIdleList'][idle]['end']
            row = (IdleListFromServer['TpaIdleList'][idle]['start'],
                   end,
                   "",
                   "",
                   ""
                   )
            tablerowdata.append(row)
        self.root.ids.idlecount.text = "Простои: "+str(idlecount)

        self.root.ids.idlelist.clear_widgets()
        layout = MDBoxLayout()
        DataTable = MDDataTable(size_hint=(1, 1),
                                use_pagination=True,
                                column_data=[
                                    ("Начало", dp(35)),
                                    ("Конец", dp(35)),
                                    ("Причина", dp(30)),
                                    ("Примечание", dp(30)),
                                    ("Наладчик", dp(20))
        ],
            row_data=tablerowdata
        )
        layout.add_widget(DataTable)
        self.root.ids.idlelist.add_widget(layout)
        log.info("Простои загружены, таблица отрисована")

    @mainthread
    def LoadEnteredWeight(self, weightlist):
        log.info("Загрузка введенного веса")
        weightcount = 0
        srweight = 0
        tablerowdata = []
        for weight in list(weightlist['EnteredWeight'].keys()):
            row = (weightlist['EnteredWeight'][weightcount]['weight'],
                   weightlist['EnteredWeight'][weightcount]['date'],
                   weightlist['EnteredWeight'][weightcount]['creator']
                   )
            srweight += float(weightlist['EnteredWeight']
                              [weightcount]['weight'])
            weightcount += 1
            tablerowdata.append(row)
        if(weightcount != 0):
            srweight = round(srweight/weightcount, 2)
        self.root.ids.enteredweight.text = "Введенный вес: "+str(weightcount)
        self.root.ids.srweight.text = str(srweight)
        self.root.ids.enteredweightlist.clear_widgets()
        layout = MDBoxLayout()
        DataTable = MDDataTable(size_hint=(1, 1),
                                use_pagination=True,
                                column_data=[
                                    ("Вес", dp(35)),
                                    ("Время", dp(35)),
                                    ("Оператор", dp(50))
        ],
            row_data=tablerowdata
        )
        layout.add_widget(DataTable)
        self.root.ids.enteredweightlist.add_widget(layout)
        log.info("Введенный вес загружен, таблица отрисована")

    @mainthread
    def LoadShiftTask(self, ShiftTaskList):
        log.info("Загрузка распоряжений")
        taskcount = 0
        tablerowdata = []
        for weight in list(ShiftTaskList['ShiftTask'].keys()):
            row = (ShiftTaskList['ShiftTask'][taskcount]['name'],
                   ShiftTaskList['ShiftTask'][taskcount]['start'],
                   ShiftTaskList['ShiftTask'][taskcount]['end']
                   )
            taskcount += 1
            tablerowdata.append(row)
        self.root.ids.shifttask.text = "Распоряжения: "+str(taskcount)

        self.root.ids.shifttasklist.clear_widgets()
        layout = MDBoxLayout()
        DataTable = MDDataTable(size_hint=(1, 1),
                                use_pagination=True,
                                column_data=[
                                    ("Вид", dp(45)),
                                    ("Начало", dp(35)),
                                    ("Конец", dp(30))
        ],
            row_data=tablerowdata
        )
        layout.add_widget(DataTable)
        self.root.ids.shifttasklist.add_widget(layout)
        log.info("Распоряжения загружены, таблица отрисована")


if __name__ == '__main__':
    MES().run()
