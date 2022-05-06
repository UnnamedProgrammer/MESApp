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
	DATENAME(YEAR, [Date]) = DATENAME(YEAR, GETDATE()) AND
	DATENAME(MONTH, [Date]) = DATENAME(MONTH, GETDATE()) AND
	DATENAME(DAY, [Date]) = DATENAME(DAY, GETDATE()) AND
	Reader = RFIDReader.Oid  AND
	[EAM_test].[dbo].[RFIDReader].Active > 0 AND
	[EAM_Iplast].[dbo].[ОбъектРемонта].Oid = [EAM_test].[dbo].[RFIDReader].Asset AND
	[EAM_test].[dbo].[MESShiftTaskData].[RepairObject] = [EAM_test].[dbo].[RFIDReader].Asset AND
	DATENAME(HOUR, [ProductionStart]) = 7 AND 
	DATENAME(YEAR, [ProductionStart]) = DATENAME(YEAR, GETDATE()) AND
	DATENAME(MONTH, [ProductionStart]) = DATENAME(MONTH, GETDATE()) AND
	DATENAME(DAY, [ProductionStart]) = DATENAME(DAY, GETDATE()) 
GROUP BY [EAM_Iplast].[dbo].[ОбъектРемонта].[Наименование], [SocketsCount], [CycleNorm], [WeightNorm]
ORDER BY [EAM_Iplast].[dbo].[ОбъектРемонта].[Наименование] ASC