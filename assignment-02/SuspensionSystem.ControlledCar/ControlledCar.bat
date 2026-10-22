@echo off
SET PATH=C:/Program Files/OpenModelica1.27.1-64bit/bin/;C:/Program Files/OpenModelica1.27.1-64bit/lib//omc;C:/Program Files/OpenModelica1.27.1-64bit/lib/;C:/Users/user1/AppData/Roaming/.openmodelica/binaries/Modelica;C:/Users/user1/AppData/Roaming/.openmodelica/libraries/Modelica 4.1.0+maint.om/Resources/Library/mingw64;C:/Users/user1/AppData/Roaming/.openmodelica/libraries/Modelica 4.1.0+maint.om/Resources/Library/ucrt64;C:/Users/user1/AppData/Roaming/.openmodelica/libraries/Modelica 4.1.0+maint.om/Resources/Library/win64;C:/Users/user1/AppData/Roaming/.openmodelica/libraries/Modelica 4.1.0+maint.om/Resources/Library;C:/Program Files/OpenModelica1.27.1-64bit/bin/;%PATH%;
SET ERRORLEVEL=
CALL "%CD%/ControlledCar.exe" %*
SET RESULT=%ERRORLEVEL%

EXIT /b %RESULT%
