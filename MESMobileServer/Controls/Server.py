from datetime import datetime
from numpy import isin
import pyodbc
import socket
import os
from .DataManipulator import DataManipulator
import pickle
from _thread import *
import struct
import time
import logging

class Server():
    def __init__(self):
        logging.info("==============Инициализация сервера==============")      
        #Словарь SQL запросов
        self.requests = {}
        #Словарь соединений к SQL базе
        self.Connections = {}
        self.ConnectionsStrings = {
            'EAM_Iplast': 'DRIVER={ODBC Driver 18 for SQL Server};SERVER=WORK2-APPSERV-8;DATABASE=EAM_Iplast;UID=terminal;PWD=xAlTeS3dGrh7;TrustServerCertificate=yes',
            'EAM_test': 'DRIVER={ODBC Driver 18 for SQL Server};SERVER=WORK2-APPSERV-8;DATABASE=EAM_test;UID=terminal;PWD=xAlTeS3dGrh7;TrustServerCertificate=yes',
            'Terminal': 'DRIVER={ODBC Driver 18 for SQL Server};SERVER=WORK2-APPSERV-8;DATABASE=EAM_test;UID=terminal;PWD=xAlTeS3dGrh7;TrustServerCertificate=yes'
        }         
        self.sock = None
        self.ip = '192.168.118.68'
        self.port = 9090
        self.clients = []
        self.runsocket = True
        self.serverstatus = ""
        self.worksthreads = {}
        self.client_sockets = []

    def DataBasesInitConnections(self):
        logging.info("=======Проверка подключения к базам данных=======")
        for Base in self.ConnectionsStrings:
            try:
                connection = pyodbc.connect(self.ConnectionsStrings[Base])
                self.Connections[Base] = connection.cursor()
                logging.info("Успешное подключение к базе: " + Base)
            except pyodbc.Error as err:
                logging.critical("Невозможно подключиться к: " + Base)
                logging.critical("Причина: " + str(err))
                self.runsocket = False


    def LoadSqlRequests(self):
        # Загрузка sql файлов в словарь для удобного выполнения запросов,
        # например Connections['EAM_Iplast'].execute(requests['GetTpaCards'])
        # получить данные запроса Connections['EAM_Iplast'].fetchone() для получения одной записи из результата
        # Connections['EAM_Iplast'].fetchall() получить все записи из результата

        logging.info("============Инициализация SQL запросов===========")
        dir = os.path.dirname(__file__)[:-9]+"\\SQL"
        files = os.listdir(dir)
        for SQLfile in files:
            sql = ""
            file = open(dir+"\\"+SQLfile, encoding='utf-8')
            text = file.read().split("\n")
            for word in text:
                sql = sql +" "+word
            self.requests[SQLfile[:-4]] = sql
            logging.info(SQLfile + " загружен.")


    def AcceptClients(self):
        # Принятие входящих подключений
        # Если подключился новый клиент, то создаётся новый поток 
        # в котором обрабатывается клиент
        self.worksthreads['AcceptClients'] = True
        self.serverstatus = "Сервер запущен"
        while(self.runsocket):
            try:
                self.sock.listen(10)
                self.serverstatus = "Обработка клиентов и ожидание подключений"
                conn, addr = self.sock.accept()
                self.serverstatus = "Подключен новый клиент"
                if(self.clients.count(addr) == 0):
                    logging.info("Подключен новый клиент:" + str(addr))
                    logging.info("Создание потока для обработки клиента:" + str(addr))
                    self.serverstatus = "Создание потока"
                    start_new_thread(self.ListenClient,(conn,addr ))
                    logging.info("Поток обработки клиента " + str(addr) + " создан.")                   
            except:               
                self.worksthreads['AcceptClients'] = False
                break
        self.worksthreads['AcceptClients'] = False

    def ListenClient(self,client,addr):
        self.client_sockets.append(client)
        self.worksthreads[str(addr)] = True
        Manupulator = None
        try:
            # Создаём SQL подключение для клиента, в случае сбоя 
            # отправим сообщение с ошибкой и завершим поток         
            connection = None
            Connections = {}
            for Base in self.ConnectionsStrings:
                try:
                    connection = pyodbc.connect(self.ConnectionsStrings[Base])
                    Connections[Base] = connection.cursor()
                except pyodbc.Error as err:
                    logging.warning("Сбой в подключении к SQL серверу")
                    logging.warning("Причина: " + str(err))
                    SQLError = {}
                    SQLError["SQLError"] = "Сбой в подключении к SQL серверу"
                    SQLError = pickle.dumps(SQLError)
                    size = len(SQLError)
                    size4bytes = struct.pack("I",size)
                    client.send(size4bytes)
                    client.send(SQLError)
                    self.worksthreads[str(addr)] = False
                    return

            Manupulator =  DataManipulator(Connections, self.requests)

            # Добавляем клиента в список клиентов
            # и отправляем первичные данные: Карточки по ТПА и список Id считывателей
            TpaCards = pickle.dumps(Manupulator.GetTpaCards('FirstConnection'))
            size = len(TpaCards)
            size4bytes = struct.pack("I",size)
            client.send(size4bytes)
            client.send(TpaCards)

            TpaReaderList = pickle.dumps(Manupulator.GetReaderIdsList())
            size = len(TpaReaderList)
            size4bytes = struct.pack("I",size)
            client.send(size4bytes)
            client.send(TpaReaderList)
            self.clients.append(addr)
        except error:
            print(error)
            self.clients.remove(addr)
            self.worksthreads[str(addr)] = False
            return

        # Получение входящих сообщений
        while(self.runsocket):
            try:
                data = client.recv(1024)
                if data:
                    client_answer = pickle.loads(data)
                    #Если данные ввиде строки
                    if(isinstance(client_answer,str)):
                        # Отправляем данные для обновления списка ТПА
                        if (client_answer == 'NeedUpdate'):
                            UpdatedTPAlist = pickle.dumps(Manupulator.GetTpaCards(client_answer))
                            logging.info("Данные от клиента: " + str(addr) + "--> " + str(client_answer)) 
                            size = len(UpdatedTPAlist)
                            size4bytes = struct.pack("I",size)
                            client.send(size4bytes)
                            client.send(UpdatedTPAlist)

                        # Если клиент вышел, удаляем его из списка и завершаем поток
                        if (client_answer == 'exit'):
                            logging.info("Клиент: " + str(addr) + " --> отключился")
                            self.clients.remove(addr)
                            self.worksthreads[str(addr)] = False
                            return

                    #Если данные виде словаря
                    elif (isinstance(client_answer,dict)):
                        #Отправка клиету данных для графика по ТПА
                        if (list(client_answer.keys())[0] == "NeedTpaDatePoints"):
                            logging.info("Данные от клиента: " + str(addr) + "--> " + str(client_answer["NeedTpaDatePoints"]))
                            graphicdata = pickle.dumps(Manupulator.GetTpaGraphPoints(client_answer["NeedTpaDatePoints"],datetime.now()))
                            size = len(graphicdata)
                            size4bytes = struct.pack("I",size)
                            client.send(size4bytes)
                            client.send(graphicdata)
                        
                        if (list(client_answer.keys())[0] == "NeedGraphHistoryPoint"):
                            logging.info("Данные от клиента: " + str(addr) + "--> " + str("NeedGraphHistoryPoint"))
                            graphicdata = pickle.dumps(Manupulator.TestGetGraphHistory(client_answer["NeedGraphHistoryPoint"]["ReaderOid"],
                                                                                        client_answer["NeedGraphHistoryPoint"]["StartDate"],
                                                                                        client_answer["NeedGraphHistoryPoint"]["EndDate"]))
                            size = len(graphicdata)
                            size4bytes = struct.pack("I",size)
                            client.send(size4bytes)
                            client.send(graphicdata)
                        
                        if(list(client_answer.keys())[0] == "NeedTpaIdle"):
                            logging.info("Данные от клиента: " + str(addr) + "--> " + str("NeedTpaIdle"))
                            idlelist = pickle.dumps(Manupulator.GetTpaIdle(client_answer["NeedTpaIdle"]))
                            size = len(idlelist)
                            size4bytes = struct.pack("I",size)
                            client.send(size4bytes)
                            client.send(idlelist)
                            

            except:
                # Если случилась непредвиденная ошибка либо не правильно отработал
                # процесс отключения, то убираем клиента из списка и завершаем поток
                self.clients.remove(addr)
                logging.info("Клиент: " + str(addr) + " --> отключился")
                self.worksthreads[str(addr)] = False
                return
        self.worksthreads[str(addr)] = False


    def ServerRun(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.ip, self.port))
        self.DataBasesInitConnections()
        if (self.runsocket):
            self.LoadSqlRequests()
            logging.info("==================Сервер запущен=================")
            self.AcceptClients()