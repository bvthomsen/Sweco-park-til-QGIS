@echo on
rmdir /s /q "%appdata%\QGIS\QGIS3\profiles\default\python\plugins\sweco_park"
call .\sweco_park\pyrcc5x.cmd
xcopy .\sweco_park\* "%appdata%\QGIS\QGIS3\profiles\default\python\plugins\sweco_park" /i /e /h /f 
