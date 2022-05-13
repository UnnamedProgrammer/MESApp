DECLARE @now datetime,  @morning datetime, @taskdate datetime, @night datetime, @shifttype int;

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
	(COUNT(RFDD.[Status]) / 2) * [SocketsCount] AS Продукт_за_смену,
	OBR.[Наименование] AS ТПА,
	STD.ProductionPlan AS План,
	STD.CycleNorm,
	STD.WeightNorm,
	STD.ProductionStart,
	STD.ProductionEnd
FROM [EAM_test].[dbo].[MESShiftTask] AS ST
	LEFT JOIN [EAM_test].[dbo].[MESShiftTaskData] AS STD ON STD.[ShiftTask] = ST.[Oid]
	LEFT JOIN [EAM_Iplast].[dbo].[ОбъектРемонта]  AS [OBR] ON STD.[RepairObject] = OBR.[Oid]
	LEFT JOIN [EAM_test].[dbo].[RFIDReader] AS RFDR ON RFDR.Asset = RepairObject
	LEFT JOIN [EAM_test].[dbo].[RFIDData] AS RFDD ON RFDD.Reader = RFDR.Oid
WHERE ST.[TaskDate] = @taskdate
	AND RFDR.Active = 1
	AND ST.[ShiftType] = @shifttype
	AND STD.[TaskStatus] IS NOT NULL AND
	DATENAME(HOUR, RFDD.[Date]) >= CAST(DATENAME(HOUR, STD.ProductionStart) AS INT) AND
	DATENAME(HOUR, RFDD.[Date]) <= CAST(DATENAME(HOUR, STD.ProductionEnd) AS INT) AND
	DATENAME(YEAR, RFDD.[Date]) = DATENAME(YEAR, STD.ProductionStart) AND
	DATENAME(MONTH, RFDD.[Date]) = DATENAME(MONTH, STD.ProductionStart) AND
	DATENAME(DAY, RFDD.[Date]) = DATENAME(DAY, STD.ProductionStart)
GROUP BY OBR.[Наименование],[STD].SocketsCount,STD.ProductionPlan,STD.CycleNorm,STD.WeightNorm,	STD.ProductionStart,STD.ProductionEnd
ORDER BY Наименование ASC