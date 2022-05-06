from datetime import datetime
import logging
import pyodbc

class DataManipulator():
    def __init__(self, Connections, requests):
        self.Connections = Connections
        self.requests = requests
        self.label_oids = []
        self.tpa_Oids = []
        self.pressforms = []
        self.production_fact_and_plans = []
        self.packet = {}
        self.startdate = datetime(
            datetime.now().year, datetime.now().month, datetime.now().day, 7)
        self.enddate = datetime(datetime.now().year,
                                datetime.now().month, datetime.now().day, 19)

    def GetTpaCards(self, status):
        '''
        Получение карточек таблицы с ТПА (аналог таблицы mes-ns) для отправки клиентам.
        Результат выполнения:
        tpa_Oids - содержит oid считывателя, наименование ТПА, его тех.состояние и Oid ТПА,
        pressforms - содержит список прессформ установленных на тпа, порядок в массиве соответствует порядку массива с ТПА,
        production_fact_and_plans - содержит в себе план продукта на смену,и фактически произведенную продукцию.
        '''
        logging.info("SQLManipulator -> GetTpaCards")
        #Забираем нужные данные из баз, и разбрасываем по спискам
        self.Connections['EAM_test'].execute(self.requests['GetTpaList'])
        query_result = self.Connections['EAM_test'].fetchall()
        self.tpa_Oids = query_result
        readers_oids = []
        buffer = []

        for i in self.tpa_Oids:
            readers_oids.append(i[0])
        for Oid in readers_oids:
            self.Connections['EAM_test'].execute("SELECT TOP (1) [Label] FROM [EAM_test].[dbo].[RFIDData]" +
                                                 " WHERE Reader = '"+Oid+"'" +
                                                 "ORDER BY Date DESC")
            buffer.append(self.Connections['EAM_test'].fetchone())
        for i in range(0, len(buffer)):
            self.label_oids.append(buffer[i][0])

        buffer = []
        for Oid in self.label_oids:
            self.Connections['EAM_test'].execute("SELECT TOP (1) [Asset] FROM [EAM_test].[dbo].[RFIDLabel] " +
                                                 "WHERE Oid LIKE '"+Oid+"'")
            buffer.append(self.Connections['EAM_test'].fetchone())
        self.label_oids = []
        for i in range(0, len(buffer)):
            self.label_oids.append(buffer[i][0])

        buffer = []
        for Oid in self.label_oids:
            if (Oid != None):
                self.Connections['EAM_test'].execute("SELECT TOP (1) [Наименование] FROM [EAM_test].[dbo].[ОбъектРемонта]" +
                                                     " WHERE Oid LIKE '"+Oid+"'")
                buffer.append(self.Connections['EAM_test'].fetchone())
            else:
                buffer.append(None)
        for pfname in buffer:
            try:
                self.pressforms.append(pfname[0])
            except:
                self.pressforms.append('None')

        self.Connections['EAM_test'].execute(
            self.requests['GetProductionPlans'])
        for Oid in self.Connections['EAM_test'].fetchall():
            self.production_fact_and_plans.append(Oid)
        buffer = []

        Tpa_cards_data = {}

        i = 0
        for tpadata in self.tpa_Oids:
            Tpa_cards_data[tpadata[1]] = [tpadata[1],
                                          tpadata[2], 'В работе', self.pressforms[i]]
            i = i + 1
        self.Connections['EAM_test'].execute(self.requests['GetTpaIdle'])
        IdleTpaList = self.Connections['EAM_test'].fetchall()
        for idle in IdleTpaList:
            Tpa_cards_data[idle[2]][2] = 'В простое'

        ReaderDurations = {}
        #Получаем средний цикл
        for reader in self.tpa_Oids:
            self.Connections['EAM_test'].execute(f'''SELECT Duration,
                                                        [Status]
                                                    FROM [EAM_test].[dbo].[RFIDData]
                                                    WHERE 
                                                        DATENAME(HOUR, [Date]) >= 7 AND 
                                                        DATENAME(HOUR, [Date]) <= 19 AND 
                                                        DATENAME(YEAR, [Date]) = DATENAME(YEAR, GETDATE()) AND
                                                        DATENAME(MONTH, [Date]) = DATENAME(MONTH, GETDATE()) AND
                                                        DATENAME(DAY, [Date]) = DATENAME(DAY, GETDATE()) AND
                                                        [Reader] = '{reader[0]}' 
                                                    ORDER BY [Date] ASC
                                                ''')
            durations = self.Connections['EAM_test'].fetchall()
            ReaderDurations[reader[1]] = durations
            durationsList = []
            if (len(ReaderDurations[reader[1]]) != 0):
                for digits in range(0, len(ReaderDurations[reader[1]])):
                    try:
                        durationsList.append(
                            ReaderDurations[reader[1]][digits][0] + ReaderDurations[reader[1]][digits+1][0])
                        ReaderDurations[reader[1]] = sum(
                            durationsList)/len(ReaderDurations[reader[1]])
                    except:
                        break
                ReaderDurations[reader[1]] = durationsList
            else:
                ReaderDurations[reader[1]] = durationsList

        for plan in self.production_fact_and_plans:
            Tpa_cards_data[plan[1]].append(str(plan[2]))
            Tpa_cards_data[plan[1]].append(str(plan[0]))
            Tpa_cards_data[plan[1]].append(str(plan[3]))
            Tpa_cards_data[plan[1]].append(str(plan[4]))

        for tpaname in ReaderDurations:
            if(len(ReaderDurations[tpaname]) > 0):
                Tpa_cards_data[tpaname].append(
                    str(ReaderDurations[tpaname][0]))
            else:
                Tpa_cards_data[tpaname].append(str(0))

        for tpas in Tpa_cards_data:
            if(len(Tpa_cards_data[tpas]) < 8):
                Tpa_cards_data[tpas].append('0')
                Tpa_cards_data[tpas].append('0')
                Tpa_cards_data[tpas].append('0')
                Tpa_cards_data[tpas].append('0')
                Tpa_cards_data[tpas].append('0')

        self.label_oids = []
        self.tpa_Oids = []
        self.pressforms = []
        self.production_fact_and_plans = []
        self.packet = {}

        # Проверка статуса подключенного клиента
        # Если NeedUpdate значит запрос от клиента который подключен давно
        # Если FirstConnection значит клиент только подключился и требует данные для отображения
        if(status == 'NeedUpdate'):
            self.packet['UpdateTpaListFromServer'] = Tpa_cards_data
        if(status == 'FirstConnection'):
            self.packet['TpaListFromServer'] = Tpa_cards_data

        return self.packet

    def GetReaderIdsList(self):
        logging.info("SQLManipulator -> GetReaderIdsList")
        TpaReaderList = {}
        packet = {}
        self.Connections['EAM_test'].execute(self.requests['GetTpaList'])
        queryresult = self.Connections['EAM_test'].fetchall()
        for id in queryresult:
            TpaReaderList[id[1]] = id[0]
        packet["TpaReaderList"] = TpaReaderList
        return packet

    def GetTpaGraphPoints(self, ReaderOid, date: datetime):
        logging.info("SQLManipulator -> GetTpaGraphPoints")
        packet = {}
        NightShift = False
        logging.info("Checking nightshift")

        # Проверка на времени смены (дневная, ночная)
        if (date.hour >= 7 and date.hour < 19):
            NightShift = False
            logging.info("not nightshift now")
        else:
            NightShift = True
            logging.info("nightshift now")

        if(NightShift == False):
            self.Connections['EAM_test'].execute(f'''
                SELECT TOP (1000)
                    [Date]
                FROM [EAM_test].[dbo].[RFIDData]
                WHERE 
                    DATENAME(HOUR, [Date]) >= 7 AND 
                    DATENAME(HOUR, [Date]) <= 19 AND 
                    DATENAME(YEAR, [Date]) = DATENAME(YEAR, GETDATE()) AND
                    DATENAME(MONTH, [Date]) = DATENAME(MONTH, GETDATE()) AND
                    DATENAME(DAY, [Date]) = DATENAME(DAY, GETDATE()) AND
                    [Reader] = '{ReaderOid}' AND
                    [Status] = 1
                ORDER BY [Date] ASC
            ''')
            resultquery = self.Connections['EAM_test'].fetchall()
            datepoints = []
            for datepoint in resultquery:
                strdate = datepoint[0].strftime("%H:%M")
                datepoints.append(strdate)
            packet["TpaDatePoints"] = datepoints
        else:
            resultqueryPartOne = []
            resultqueryPartTwo = []
            self.Connections['EAM_test'].execute(f'''
                SELECT TOP (1000)
                    [Date]
                FROM [EAM_test].[dbo].[RFIDData]
                WHERE 
                    DATENAME(HOUR, [Date]) >= 19 AND 
                    DATENAME(HOUR, [Date]) <= 23 AND 
                    DATENAME(YEAR, [Date]) = DATENAME(YEAR, GETDATE()) AND
                    DATENAME(MONTH, [Date]) = DATENAME(MONTH, GETDATE()) AND
                    DATENAME(DAY, [Date]) = DATENAME(DAY, DATEADD(DAY,-2,GETDATE())) AND
                    [Reader] = '{ReaderOid}' AND
                    [Status] = 1
                ORDER BY [Date] ASC
                ''')
            resultqueryPartOne = self.Connections['EAM_test'].fetchall()

            self.Connections['EAM_test'].execute(f'''
                SELECT TOP (1000)
                    [Date]
                FROM [EAM_test].[dbo].[RFIDData]
                WHERE 
                    DATENAME(HOUR, [Date]) >= 0 AND 
                    DATENAME(HOUR, [Date]) <= 7 AND 
                    DATENAME(YEAR, [Date]) = DATENAME(YEAR, GETDATE()) AND
                    DATENAME(MONTH, [Date]) = DATENAME(MONTH, GETDATE()) AND
                    DATENAME(DAY, [Date]) = DATENAME(DAY, DATEADD(DAY,-1,GETDATE())) AND
                    [Reader] = '{ReaderOid}' AND
                    [Status] = 1
                ORDER BY [Date] ASC
                ''')
            resultqueryPartTwo = self.Connections['EAM_test'].fetchall()

            resultquery = resultqueryPartOne + resultqueryPartTwo
            datepoints = []
            for datepoint in resultquery:
                strdate = datepoint[0].strftime("%H:%M")
                datepoints.append(strdate)
            packet["TpaDatePoints"] = datepoints
        return packet

    def TestGetGraphHistory(self, ReaderOid, datestart: datetime, dateend: datetime):
        logging.info("SQLManipulator -> TestGetGraphHistory")
        packet = {}
        NightShift = False
        logging.info("Checking nightshift")

        # Проверка времени смены (дневная, ночная)
        if (datestart.hour >= 7 and datestart.hour < 19):
            NightShift = False
            logging.info("not nightshift now")
        else:
            NightShift = True
            logging.info("nightshift now")

        if(NightShift == False):
            self.Connections['EAM_test'].execute(f'''
                SELECT TOP (1000)
                    [Date]
                FROM [EAM_test].[dbo].[RFIDData]
                WHERE 
                    DATENAME(HOUR, [Date]) >= 7 AND 
                    DATENAME(HOUR, [Date]) <= 19 AND 
                    DATENAME(YEAR, [Date]) = DATENAME(YEAR, '{datestart}') AND
                    DATENAME(MONTH, [Date]) = DATENAME(MONTH, '{datestart}') AND
                    DATENAME(DAY, [Date]) = DATENAME(DAY, '{datestart}') AND
                    [Reader] = '{ReaderOid}' AND
                    [Status] = 1
                ORDER BY [Date] ASC
            ''')
            resultquery = self.Connections['EAM_test'].fetchall()
            datepoints = []
            for datepoint in resultquery:
                strdate = datepoint[0].strftime("%H:%M")
                datepoints.append(strdate)

        else:
            resultqueryPartOne = []
            resultqueryPartTwo = []
            self.Connections['EAM_test'].execute(f'''
                SELECT TOP (1000)
                    [Date]
                FROM [EAM_test].[dbo].[RFIDData]
                WHERE 
                    DATENAME(HOUR, [Date]) >= 19 AND 
                    DATENAME(HOUR, [Date]) <= 23 AND 
                    DATENAME(YEAR, [Date]) = DATENAME(YEAR, '{datestart}') AND
                    DATENAME(MONTH, [Date]) = DATENAME(MONTH, '{datestart}') AND
                    DATENAME(DAY, [Date]) = DATENAME(DAY, '{datestart}') AND
                    [Reader] = '{ReaderOid}' AND
                    [Status] = 1
                ORDER BY [Date] ASC
                ''')
            resultqueryPartOne = self.Connections['EAM_test'].fetchall()

            self.Connections['EAM_test'].execute(f'''
                SELECT TOP (1000)
                    [Date]
                FROM [EAM_test].[dbo].[RFIDData]
                WHERE 
                    DATENAME(HOUR, [Date]) >= 0 AND 
                    DATENAME(HOUR, [Date]) <= 7 AND 
                    DATENAME(YEAR, [Date]) = DATENAME(YEAR, '{dateend}') AND
                    DATENAME(MONTH, [Date]) = DATENAME(MONTH, '{dateend}') AND
                    DATENAME(DAY, [Date]) = DATENAME(DAY, '{dateend}') AND
                    [Reader] = '{ReaderOid}' AND
                    [Status] = 1
                ORDER BY [Date] ASC
                ''')
            resultqueryPartTwo = self.Connections['EAM_test'].fetchall()

            resultquery = resultqueryPartOne + resultqueryPartTwo
            datepoints = []
            for datepoint in resultquery:
                strdate = datepoint[0].strftime("%H:%M")
                datepoints.append(strdate)

        if(NightShift == False):
            self.Connections['EAM_test'].execute(f'''
                                SELECT	((COUNT([Status]) / 2) * [SocketsCount]) AS Продукт_за_смену,
                                        [EAM_Iplast].[dbo].[ОбъектРемонта].[Наименование] as ТПА,
                                        SUM(DISTINCT [ProductionPlan]) AS План,
                                        [CycleNorm],
                                        [WeightNorm]
                                FROM [EAM_test].[dbo].[RFIDData],
                                        [EAM_test].[dbo].[RFIDReader],
                                        [EAM_Iplast].[dbo].[ОбъектРемонта],
                                        [EAM_test].[dbo].[MESShiftTaskData]
                                WHERE
                                    DATENAME(HOUR, [Date]) >= 7 AND 
                                    DATENAME(HOUR, [Date]) <= 19 AND 
                                    DATENAME(YEAR, [Date]) = DATENAME(YEAR, '{datestart}') AND
                                    DATENAME(MONTH, [Date]) = DATENAME(MONTH, '{datestart}') AND
                                    DATENAME(DAY, [Date]) = DATENAME(DAY, '{datestart}') AND 
                                    Reader = RFIDReader.Oid  AND
                                    [EAM_test].[dbo].[RFIDReader].Active > 0 AND
                                    [EAM_Iplast].[dbo].[ОбъектРемонта].Oid = [EAM_test].[dbo].[RFIDReader].Asset AND
                                    [EAM_test].[dbo].[MESShiftTaskData].[RepairObject] = [EAM_test].[dbo].[RFIDReader].Asset AND
                                    DATENAME(HOUR, [ProductionStart]) = {datestart.hour} AND 
                                    DATENAME(YEAR, [ProductionStart]) = DATENAME(YEAR, '{datestart}') AND
                                    DATENAME(MONTH, [ProductionStart]) = DATENAME(MONTH, '{datestart}') AND
                                    DATENAME(DAY, [ProductionStart]) = DATENAME(DAY, '{datestart}') 
                                GROUP BY [EAM_Iplast].[dbo].[ОбъектРемонта].[Наименование], [SocketsCount], [CycleNorm], [WeightNorm]
                                ORDER BY [EAM_Iplast].[dbo].[ОбъектРемонта].[Наименование] ASC 
                                ''')
            plans = self.Connections['EAM_test'].fetchall()
            dict_plans = {}
            for plan in plans:
                dict_plans[plan[1]] = {"count": plan[0], "plan": plan[2]}
            packet["HistoryDatePoints"] = datepoints
            packet["Plan"] = dict_plans
        else:
            self.Connections['EAM_test'].execute(f'''
                                SELECT	((COUNT([Status]) / 2) * [SocketsCount]) AS Продукт_за_смену,
                                        [EAM_Iplast].[dbo].[ОбъектРемонта].[Наименование] as ТПА,
                                        SUM(DISTINCT [ProductionPlan]) AS План,
                                        [CycleNorm],
                                        [WeightNorm]
                                FROM [EAM_test].[dbo].[RFIDData],
                                        [EAM_test].[dbo].[RFIDReader],
                                        [EAM_Iplast].[dbo].[ОбъектРемонта],
                                        [EAM_test].[dbo].[MESShiftTaskData]
                                WHERE
                                    DATENAME(HOUR, [Date]) >= 19 AND 
                                    DATENAME(HOUR, [Date]) <= 23 AND 
                                    DATENAME(YEAR, [Date]) = DATENAME(YEAR, '{datestart}') AND
                                    DATENAME(MONTH, [Date]) = DATENAME(MONTH, '{datestart}') AND
                                    DATENAME(DAY, [Date]) = DATENAME(DAY, '{datestart}') AND 
                                    Reader = RFIDReader.Oid  AND
                                    [EAM_test].[dbo].[RFIDReader].Active > 0 AND
                                    [EAM_Iplast].[dbo].[ОбъектРемонта].Oid = [EAM_test].[dbo].[RFIDReader].Asset AND
                                    [EAM_test].[dbo].[MESShiftTaskData].[RepairObject] = [EAM_test].[dbo].[RFIDReader].Asset AND
                                    DATENAME(HOUR, [ProductionStart]) = {datestart.hour} AND 
                                    DATENAME(YEAR, [ProductionStart]) = DATENAME(YEAR, '{datestart}') AND
                                    DATENAME(MONTH, [ProductionStart]) = DATENAME(MONTH, '{datestart}') AND
                                    DATENAME(DAY, [ProductionStart]) = DATENAME(DAY, '{datestart}') 
                                GROUP BY [EAM_Iplast].[dbo].[ОбъектРемонта].[Наименование], [SocketsCount], [CycleNorm], [WeightNorm]
                                ORDER BY [EAM_Iplast].[dbo].[ОбъектРемонта].[Наименование] ASC 
                                ''')
            plans = self.Connections['EAM_test'].fetchall()
            dict_plans = {}
            for plan in plans:
                dict_plans[plan[1]] = {"count": plan[0], "plan": plan[2]}

            self.Connections['EAM_test'].execute(f'''
                                SELECT	((COUNT([Status]) / 2) * [SocketsCount]) AS Продукт_за_смену,
                                        [EAM_Iplast].[dbo].[ОбъектРемонта].[Наименование] as ТПА,
                                        SUM(DISTINCT [ProductionPlan]) AS План,
                                        [CycleNorm],
                                        [WeightNorm]
                                FROM [EAM_test].[dbo].[RFIDData],
                                        [EAM_test].[dbo].[RFIDReader],
                                        [EAM_Iplast].[dbo].[ОбъектРемонта],
                                        [EAM_test].[dbo].[MESShiftTaskData]
                                WHERE
                                    DATENAME(HOUR, [Date]) >= 0 AND 
                                    DATENAME(HOUR, [Date]) <= 7 AND 
                                    DATENAME(YEAR, [Date]) = DATENAME(YEAR, '{datestart}') AND
                                    DATENAME(MONTH, [Date]) = DATENAME(MONTH, '{datestart}') AND
                                    DATENAME(DAY, [Date]) = DATENAME(DAY, '{datestart}') AND 
                                    Reader = RFIDReader.Oid  AND
                                    [EAM_test].[dbo].[RFIDReader].Active > 0 AND
                                    [EAM_Iplast].[dbo].[ОбъектРемонта].Oid = [EAM_test].[dbo].[RFIDReader].Asset AND
                                    [EAM_test].[dbo].[MESShiftTaskData].[RepairObject] = [EAM_test].[dbo].[RFIDReader].Asset AND
                                    DATENAME(HOUR, [ProductionStart]) = {datestart.hour} AND 
                                    DATENAME(YEAR, [ProductionStart]) = DATENAME(YEAR, '{datestart}') AND
                                    DATENAME(MONTH, [ProductionStart]) = DATENAME(MONTH, '{datestart}') AND
                                    DATENAME(DAY, [ProductionStart]) = DATENAME(DAY, '{datestart}') 
                                GROUP BY [EAM_Iplast].[dbo].[ОбъектРемонта].[Наименование], [SocketsCount], [CycleNorm], [WeightNorm]
                                ORDER BY [EAM_Iplast].[dbo].[ОбъектРемонта].[Наименование] ASC 
                                ''')
            plans = self.Connections['EAM_test'].fetchall()
            for plan in plans:
                try:
                    dict_plans[plan[1]]["count"] += plan[0]
                except:
                    continue
            packet["HistoryDatePoints"] = datepoints
            packet["Plan"] = dict_plans

        return packet

    # Запрос вытаскивающий простои ТПА
    def GetTpaIdle(self,repobj):
        # try:
        nightshift = False
        # Проверка на времени смены (дневная, ночная)
        if (datetime.now().hour >= 7 and datetime.now().hour < 19):
            nightshift = False
        else:
            nightshift = True
        
        if(nightshift == False):
            query = f''' 
                SELECT [MESIdleJournal].[Oid]
                    ,[MESIdleJournal].[RepairObject]
                    ,[MESIdleJournal].[StartDate]
                    ,[MESIdleJournal].[EndDate]
                    ,[Asset]
                FROM [EAM_test].[dbo].[MESIdleJournal],
                    [EAM_test].[dbo].[RFIDReader]
                WHERE 
                    DATENAME(HOUR, [MESIdleJournal].[StartDate]) >= 7 AND 
                    DATENAME(HOUR, [MESIdleJournal].[StartDate]) <= 19 AND 
                    DATENAME(YEAR, [MESIdleJournal].[StartDate]) = DATENAME(YEAR, GETDATE()) AND
                    DATENAME(MONTH, [MESIdleJournal].[StartDate]) = DATENAME(MONTH, GETDATE()) AND
                    DATENAME(DAY, [MESIdleJournal].[StartDate]) = DATENAME(DAY, GETDATE()) AND	
                    [RFIDReader].Oid = '{repobj}' AND
                    [MESIdleJournal].[RepairObject] = Asset
                ORDER BY [MESIdleJournal].StartDate DESC
            '''
            self.Connections['EAM_test'].execute(query)
            result = self.Connections['EAM_test'].fetchall()
            editresult = {'TpaIdleList': {},'EnteredWeight': {}}
            if (len(result) > 0):
                for idle in result:
                    editresult['TpaIdleList'][idle[0]] = {
                        'Tpa': idle[1],
                        'start': idle[2],
                        'end': idle[3]
                    }
            EnteredWeight = self.GetTpaWeight(repobj)
            i = 0
            print(EnteredWeight)
            if(EnteredWeight != []):
                for weight in EnteredWeight:
                    print(weight)
                    if(weight[0] == None and 
                       weight[1] == None and 
                       weight[2] == None):
                       continue
                    editresult['EnteredWeight'][i] = {
                        'weight': weight[0],
                        'date': weight[1],
                        'creator': weight[2]
                    }
                    i += 1

        # except pyodbc.Error as e:
        #     print(e)
        #     return
        return editresult

    # Метод для вытаскивания введенного веса ТПА
    def GetTpaWeight(self,repobj):
        nightshift = False
        # Проверка на времени смены (дневная, ночная)
        if (datetime.now().hour >= 7 and datetime.now().hour < 19):
            nightshift = False
        else:
            nightshift = True
        
        if(nightshift == False):
            query = f''' 
                        DECLARE @now datetime,  @morning datetime, @taskdate datetime, @night datetime, @shifttype int ;
                                                            
                        SET @now = GETDATE();
                        SET @morning = DATEADD( hour, 7, DATEDIFF( dd, 0, @now ) );
                        SET @night = DATEADD( hour, 19, DATEDIFF( dd, 0, @now ) );
                                                            
                        IF @now >= @morning AND @now < @night
                            SET @shifttype = 0;
                        ELSE 
                            SET @shifttype = 1;
                                                            
                        IF @now >= @morning
                            SET @taskdate = CAST( @now AS date );
                        ELSE 
                            SET @taskdate = DATEADD(DAY, -1, CAST( @now AS date ));
                                                                        
                        SELECT  
                            MSW.[Weight],
                            MSW.[CreateDate],
                            EMPLE.Наименование,
                            RDOID.Oid
                        FROM [EAM_test].[dbo].[MESShiftTask] AS ST
                        LEFT JOIN [EAM_test].[dbo].[MESShiftTaskData] AS STD ON STD.[ShiftTask] = ST.[Oid]
                        LEFT JOIN [EAM_Iplast].[dbo].[ОбъектРемонта]  AS [OBR] ON STD.[RepairObject] = OBR.[Oid]
                        LEFT JOIN [EAM_test].[dbo].[MESShiftWeight] AS MSW ON MSW.ShiftTaskData = STD.Oid
                        LEFT JOIN [EAM_test].[dbo].[БазовыйРесурс] AS EMPLE ON EMPLE.[Oid] = MSW.Creator
                        LEFT JOIN [EAM_test].[dbo].[RFIDReader] AS RDOID ON RDOID.Asset = RepairObject
                        WHERE ST.[TaskDate] = @taskdate 
                        AND ST.[ShiftType] = @shifttype
                        AND STD.[TaskStatus] IS NOT NULL
                        AND RDOID.Active = 1
                        AND RDOID.Oid = '{repobj}'
            '''
            self.Connections['EAM_test'].execute(query)
            result = self.Connections['EAM_test'].fetchall()
        return result