from kivymatplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
from kivymd.uix.boxlayout import MDBoxLayout
import matplotlib.dates as dates
import datetime as dt
from datetime import date, datetime, timedelta
import numpy as np
from kivy.metrics import dp
import math


class DetailGraph(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.xpoints = None
        self.ypoints = None
        self.diff = 0
        self.xfactpoints = None
        self.yfactpoints = None
        self.productfact = 0
        self.orientation = "vertical"
        self.pos_hint = {'center_x': .5, 'center_y': .5}
        self.padding = (dp(5), dp(5), dp(5), dp(5))
        self.TimeToEndPlan = None
        self.oldEndTime = None

    # Метод построения графика статистики по машине
    def LoadGraph(self, datepointsdict, productplan, productfact):
        self.clear_widgets()
        productpoints = []
        self.productfact = productfact
        count = 0
        datepoints = datepointsdict['TpaDatePoints']
        for time in datepoints:
            count += 1
            productpoints.append(count)

        #Фактические точки с сервера
        self.yfactpoints = productpoints
        self.xfactpoints = [dt.datetime.strptime(
            i, "%H:%M") for i in datepoints]

        #Плановые точки
        if (datetime.now().hour >= 7 and datetime.now().hour < 19):
            self.xpoints = self.makedate('7:00', '19:00')
        else:
            self.xpoints = self.makedate('19:00', '7:00')
        fig, ax = plt.subplots()
        if(int(productplan) > 0):
            self.ypoints = [math.floor(i*int(productplan)/len(self.xpoints))
                            for i in range(0, len(self.xpoints))]
            formatter = dates.DateFormatter('%H:%M')
            ax.xaxis.set_major_formatter(formatter)
            ax.xaxis.set_major_locator(dates.HourLocator())

            #Установка параметров сетки и размера шрифта
            plt.grid(which='minor', alpha=0.2)
            plt.grid(which='major', alpha=0.5)
            plt.tick_params(axis='x', which='major', labelsize=dp(9))
            plt.tick_params(axis='y', which='major', labelsize=dp(9))

            #Установка лимитов
            ax.set_ylim([0, int(productplan)])
            if (datetime.now().hour >= 7 and datetime.now().hour < 19):
                # Если дневная смена
                ax.set_xlim([dt.datetime.strptime("7:00", "%H:%M"),
                            dt.datetime.strptime("19:00", "%H:%M")])
                xlabels = ["7:00", "8:00", "9:00", "10:00", "11:00", "12:00",
                           "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"]
            else:
                # Если ночная
                ax.set_xlim([dt.datetime.strptime("19:00", "%H:%M"),
                            dt.datetime.strptime("7:00", "%H:%M") + timedelta(days=1)])
                xlabels = ["19:00", "20:00", "21:00", "22:00", "23:00", "00:00",
                           "01:00", "02:00", "03:00", "04:00", "05:00", "06:00", "07:00"]

            ax.set_xticklabels(xlabels, rotation=45)

            #Установка шага для осей
            plt.yticks(np.arange(0, int(productplan), int(productplan)/12))
            plt.fill_between(self.makedate(dt.datetime.strftime(dt.datetime.now(), "%H:%M"), "19:00"), int(
                productplan), np.zeros_like(int(productplan)), color='#679FD2')

        #Формирование графика
        if(datepoints != []):
            plt.plot(self.xpoints, self.ypoints, color="#408DD2", linewidth=dp(2))
            plt.plot(self.xfactpoints, self.yfactpoints,
                    color="#28A745", linewidth=dp(2))
            self.diff = self.getDiff()
        graph = FigureCanvasKivyAgg(plt.gcf())
        self.add_widget(graph)
        self.TimeToEndPlan = self.GetEndPlan(productplan, productfact)
        plt.close(fig)

    # Метод формирования графика за прошлые смены
    def LoadGraphHistory(self, enddate, startdate, points, plan):
        self.clear_widgets()
        formatter = dates.DateFormatter('%H:%M')
        fig, ax = plt.subplots()

        count = 0
        productpoints = []
        datepoints = points["HistoryDatePoints"]
        for time in datepoints:
            count += 1
            productpoints.append(count)

        # Фактические точки с сервера
        self.yfactpoints = productpoints
        self.xfactpoints = [dt.datetime.strptime(
            i, "%H:%M") for i in datepoints]
        modifyfactpoints = []

        if (startdate.hour >= 7 and startdate.hour < 19):
            pass
        else:
            for i in self.xfactpoints:
                if(i.hour >= 0 and i.hour <= 7):
                    i = i + timedelta(days=1)
                modifyfactpoints.append(i)
            self.xfactpoints = modifyfactpoints

        #Установка параметров сетки и размера шрифта
        plt.grid(which='minor', alpha=0.2)
        plt.grid(which='major', alpha=0.5)
        plt.tick_params(axis='x', which='major', labelsize=dp(9))
        plt.tick_params(axis='y', which='major', labelsize=dp(9))
        ax.xaxis.set_major_formatter(formatter)
        ax.xaxis.set_major_locator(dates.HourLocator())

        # Плановые точки по оси X (Время смены)
        if (startdate.hour >= 7 and startdate.hour < 19):
            self.xpoints = self.makedate('7:00', '19:00')
        else:
            self.xpoints = self.makedate('19:00', '7:00')
        # Плановые точки по оси Y (план продукта)
        self.ypoints = [math.floor(i*int(plan)/len(self.xpoints))
                        for i in range(0, len(self.xpoints))]
        #Установка лимитов
        ax.set_ylim([0, int(plan)])

        if (startdate.hour >= 7 and startdate.hour < 19):
            # Если дневная смена
            ax.set_xlim([dt.datetime.strptime("7:00", "%H:%M"),
                        dt.datetime.strptime("19:00", "%H:%M")])
            xlabels = ["7:00", "8:00", "9:00", "10:00", "11:00", "12:00",
                       "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"]
        else:
            # Если ночная
            ax.set_xlim([dt.datetime.strptime("19:00", "%H:%M"),
                        dt.datetime.strptime("7:00", "%H:%M") + timedelta(days=1)])
            xlabels = ["19:00", "20:00", "21:00", "22:00", "23:00", "00:00",
                       "01:00", "02:00", "03:00", "04:00", "05:00", "06:00", "07:00"]
        #Установка шага для оси Y
        plt.yticks(np.arange(0, int(plan), int(plan)/12))

        #Формирование графика
        plt.plot(self.xpoints, self.ypoints, color="#408DD2", linewidth=dp(2))
        plt.plot(self.xfactpoints, self.yfactpoints,
                 color="#28A745", linewidth=dp(2))
        ax.set_xticklabels(xlabels, rotation=45)
        graph = FigureCanvasKivyAgg(plt.gcf())
        self.add_widget(graph)
        plt.close(fig)
    # Создание дат для отображения плановой линии

    def makedate(self, start, end):
        datelist = []
        if(start == "7:00" and end == "19:00"):
            startd = dt.datetime.strptime(start, "%H:%M")
            endd = dt.datetime.strptime(end, "%H:%M")
        else:
            startd = dt.datetime.strptime(start, "%H:%M")
            endd = dt.datetime.strptime(end, "%H:%M")+timedelta(days=1)

        while(startd != endd):
            datelist.append(startd)
            startd = startd + timedelta(minutes=1)
        return datelist

    # Получение перпендикулярной прямой к оси Ox пересекающая плановую линию и фактическую
    # тем самым вычисляется растояние между этими линиями  являющаяеся отклонением
    def getDiff(self):
        datenowstring = dt.datetime.strftime(dt.datetime.now(), "%H:%M")
        datenowd = dt.datetime.strptime(datenowstring, "%H:%M")
        i = 0
        for point in self.xpoints:
            i = i + 1
            if point == datenowd:
                break

        return str(int(math.floor(float(self.productfact) - float(self.ypoints[i]))))

    # Вычисление поля "До конца плана"
    # Получаем две точки даты с разницой в 10-20 минут, и количество продукции произведенное в эти моменты времени,
    # разница количества продукции и будет количеством произведенное за 10-20 минут, далее вичитаем
    # из плана продукта факт продукта, получиться количество которое необходимо произвести, зная сколько продукции
    # мы делаем за 10-20 минут, высчитываем количество производимого продукта в минуту, зная количество продукта в минуту
    # и нужное количество продукта которое осталось произвести высчитываем время за которое машина с данной скоростью
    # произведет продукцию до конца плана
    def GetEndPlan(self, productplan, productfact):
        points = self.xfactpoints
        FiveMinutesAgo = datetime(1900, 1, 1, datetime.now().hour, datetime.now(
        ).minute, datetime.now().second) - timedelta(minutes=10)
        points.append(FiveMinutesAgo)
        points.sort()
        firstdate = None
        secondate = None
        for i in range(0, len(points)):
            if points[i] == FiveMinutesAgo:
                try:
                    firstdate = [points[i + 1], i+1]
                    firstcount = self.yfactpoints[i+1]
                except:
                    firstdate = 0
                try:
                    secondate = [points[i - 1], i-1]
                    secondcount = self.yfactpoints[i-1]
                except:
                    secondate = 0

        if(firstdate != 0 and secondate != 0):
            datediff = firstdate[0] - secondate[0]
            minutes = datediff.total_seconds()/60
            totalcount = firstcount - secondcount
            countperminute = totalcount/minutes
            planendofminutes = (
                int(productplan)-int(productfact))/countperminute
            time_now = datetime(1900, 1, 1, datetime.now(
            ).hour, datetime.now().minute, datetime.now().second)
            time_to_end = time_now + timedelta(minutes=planendofminutes)
            end_time_result = time_to_end - time_now
            self.oldEndTime = end_time_result
            return str(end_time_result)
        else:
            if(self.oldEndTime == None):
                return "Неизвестно"
            else:
                return str(self.oldEndTime)
