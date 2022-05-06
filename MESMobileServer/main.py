import os
import logging
from datetime import datetime

fdir = dir = os.path.dirname(__file__) + "\\logs\\"
filename = r'Log_at_'+datetime.strftime(datetime.now(),'%Y-%m-%d %H-%M-%S')+'.txt'
os.path.join(fdir,filename)
open(fdir+filename, 'w',encoding="utf-8").close()


logging.basicConfig(
    level=logging.INFO,
    encoding="utf-8",
    filename= fdir+filename,
    format= "%(asctime)s - %(levelname)s - %(message)s",
    datefmt='%H:%M:%S'
)

from concurrent.futures import thread
from kivy.config import Config
Config.set('graphics', 'width', '300')
Config.set('graphics', 'height', '500')
Config.set('graphics', 'resizable', False)

from threading import main_thread
from Controls.Server import Server
from kivymd.app import MDApp
from _thread import *
from kivy.lang.builder import Builder
from kivymd.uix.list import OneLineIconListItem,IconLeftWidget
from kivy.clock import mainthread
from kivy.utils import get_color_from_hex
import socket
import time
import os

KV = '''
Screen:
    md_bg_color: (1,1,1,1,1)
    MDBoxLayout: 
        orientation: 'vertical'
        MDBoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            padding: 0,0,0,15
            MDLabel:
                id: status
                halign: 'center'
                text: "Статус: Выключен" 
                size: self.texture_size

            MDRaisedButton:
                id: but
                text: "Запуск"
                pos_hint: {'center_x': .5, 'center_y': .5}
                on_press: app.ServerStart()
                md_bg_color: app.change_color("#37DB79")

        MDSeparator:  

        MDBoxLayout:
            size_hint_y: None
            size: (d.texture_size[0], d.texture_size[1] + 15)
            MDLabel:
                id:d
                halign: 'center'
                text: "Подключенные пользователи" 
                size: self.texture_size    

        MDSeparator:  

        ScrollView:
            do_scroll_x: False
            do_scroll_y: True
            MDBoxLayout:
                id: client_list
                default_size_hint: 1, None
                size_hint_y: None
                orientation: 'vertical'
                height: self.minimum_height
'''

class MESMobileServer(MDApp):
    def __init__(self):
        super().__init__()
        logging.info("Запуск серверной программы.")
        self.MobileServer = Server()
        self._app_window
        self.status = self.MobileServer.serverstatus
        self.manageractive = True

    def build(self):
        logging.info("Загрузка KV макета.")
        return Builder.load_string(KV)

    def ServerStart(self):
        if (self.root.ids.but.text == "Запуск"):
            logging.info("Нажата кнопка 'Запуск'.")
            self.root.ids.client_list.clear_widgets
            self.root.ids.but.md_bg_color = self.change_color("#FF1800")
            self.root.ids.but.text = "Выключить"
            self.root.ids.status.text = "Статус: Включен"
            self.manageractive = True
            self.MobileServer.runsocket = True
            self.MobileServer.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            start_new_thread(self.MobileServer.ServerRun,())
            start_new_thread(self.clientmanager,())
            logging.info("Кнопка отработала успешно")
        else:
            logging.info("Нажата кнопка 'Выключить'.")
            self.root.ids.status.text = "Статус: Завершение потоков"
            self.manageractive = False
            self.MobileServer.runsocket = False
            while(self.MobileServer.worksthreads["AcceptClients"] == True):
                  self.MobileServer.sock.close()
            for i in range(0, len(self.MobileServer.client_sockets)):
                self.MobileServer.client_sockets[i].close()
            self.root.ids.but.md_bg_color = self.change_color("#37DB79")
            self.root.ids.but.text = "Запуск"
            self.root.ids.status.text = "Статус: Выключен"
            logging.info("Кнопка отработала успешно.")

    def clientmanager(self):
        old_clients_count = len(self.MobileServer.clients)
        while(self.manageractive):
            time.sleep(1)
            self.status = self.MobileServer.serverstatus
            if(old_clients_count < len(self.MobileServer.clients)):
                logging.info("Добавление клиента в список.")
                self.clear_client_field()
                old_clients_count = len(self.MobileServer.clients)
                for client in self.MobileServer.clients:
                    self.AddClient(client)
                logging.info("Клиент успешно добавлен.")

            if(old_clients_count > len(self.MobileServer.clients)):
                logging.info("Клиент отключился. Удаление из списка.")
                self.clear_client_field()
                old_clients_count = len(self.MobileServer.clients)
                for client in self.MobileServer.clients:
                    self.AddClient(client)  
                logging.info("Клиент успешно удалён из списка.")

    @mainthread
    def AddClient(self,client):
        list_item = OneLineIconListItem(text=str(client))
        list_item.add_widget(IconLeftWidget(icon="account"))
        self.root.ids.client_list.add_widget(list_item)

    @mainthread
    def clear_client_field(self):
        self.root.ids.client_list.clear_widgets()

    def change_color(self,color):
        return get_color_from_hex(color)

    def on_start(self):
        pass

if __name__ == "__main__":
    MESMobileServer().run()

