SELECT	
	EAM_test.dbo.RFIDReader.Oid AS ReaderOid,
	EAM_Iplast.dbo.ОбъектРемонта.Наименование,
	EAM_test.dbo.ТехническоеСостояние.Наименование,
	PF.Наименование
FROM 
	EAM_test.dbo.RFIDReader,
	EAM_Iplast.dbo.ОбъектРемонта,
	EAM_test.dbo.ТехническоеСостояние,
	[EAM_test].[dbo].[RFIDData],
	[EAM_test].[dbo].[RFIDLabel] AS RL
	LEFT JOIN EAM_Iplast.dbo.ОбъектРемонта AS PF ON PF.Oid = RL.Asset
WHERE 
	EAM_Iplast.dbo.ОбъектРемонта.Oid = EAM_test.dbo.RFIDReader.Asset 
		AND
	RFIDReader.Asset  IS NOT NULL 
		AND 
	RFIDReader.Active > 0
		AND
	ТехническоеСостояние.Oid = EAM_Iplast.dbo.ОбъектРемонта.ТехСостояние AND
	[EAM_test].[dbo].[RFIDData].[Date] = (SELECT MAX([EAM_test].[dbo].[RFIDData].[Date]) 
										  FROM [EAM_test].[dbo].[RFIDData] 
										  WHERE [EAM_test].[dbo].[RFIDData].Reader = EAM_test.dbo.RFIDReader.Oid) AND
	RL.Oid = [EAM_test].[dbo].[RFIDData].[Label]
ORDER BY EAM_Iplast.dbo.ОбъектРемонта.Наименование ASC