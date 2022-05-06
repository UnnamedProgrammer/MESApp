SELECT 
	EAM_test.dbo.RFIDReader.Oid AS ReaderOid,
	EAM_Iplast.dbo.ОбъектРемонта.Наименование,
	EAM_test.dbo.ТехническоеСостояние.Наименование,
	EAM_test.dbo.RFIDReader.Asset
FROM 
	EAM_test.dbo.RFIDReader,
	EAM_Iplast.dbo.ОбъектРемонта,
	EAM_test.dbo.ТехническоеСостояние
WHERE 
	EAM_Iplast.dbo.ОбъектРемонта.Oid = EAM_test.dbo.RFIDReader.Asset 
		AND
	RFIDReader.Asset  IS NOT NULL 
		AND 
	RFIDReader.Active > 0
		AND
	ТехническоеСостояние.Oid = EAM_Iplast.dbo.ОбъектРемонта.ТехСостояние
ORDER BY ОбъектРемонта.Наименование ASC 