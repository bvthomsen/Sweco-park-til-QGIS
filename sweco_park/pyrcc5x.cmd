@echo on
set qprogdir="C:\Program Files\QGIS 3.10\bin"
call %qprogdir%\o4w_env.bat"
call %qprogdir%\qt5_env.bat"
call %qprogdir%\py3_env.bat"
@echo on
pyrcc5 -o %0\..\resources.py %0\..\resources.qrc
