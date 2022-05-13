SELECT TOP (1000)
      MAX([Date]) AS [MaxDate],
      [RFIDReader].Oid AS RFIDReaderOid,
      [EAM_test].[dbo].[ОбъектРемонта].Наименование
FROM [EAM_test].[dbo].[RFIDData], [EAM_test].[dbo].[RFIDReader], [EAM_test].[dbo].[ОбъектРемонта]
WHERE Reader = [RFIDReader].Oid AND
      ([RFIDReader].Active > 0 AND
      [RFIDReader].Active IS NOT NULL) AND
      [RFIDReader].Asset IS NOT NULL AND
      [EAM_test].[dbo].[ОбъектРемонта].Oid = [RFIDReader].Asset
GROUP BY [RFIDReader].Oid,[ОбъектРемонта].Наименование
HAVING DATEDIFF(MINUTE, MAX([Date]), GETDATE()) > 10
ORDER BY [ОбъектРемонта].Наименование