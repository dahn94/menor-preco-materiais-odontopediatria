@echo off
REM Script de instalação para Windows do Sistema de Comparação de Preços
setlocal enabledelayedexpansion

echo ===============================================
echo Sistema de Comparacao de Precos - Instalador
echo ===============================================
echo.

REM Verificar se Python está instalado
echo [1/5] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Por favor, instale Python 3.7 ou superior de:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Obter versão do Python
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo SUCESSO: Python %PYTHON_VERSION% encontrado

REM Verificar Tkinter
echo [2/5] Verificando Tkinter...
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo ERRO: Tkinter nao encontrado!
    echo Por favor, reinstale Python marcando a opcao "tcl/tk and IDLE"
    pause
    exit /b 1
)
echo SUCESSO: Tkinter encontrado

REM Criar diretório de instalação
echo [3/5] Criando diretorios...
set INSTALL_DIR=%USERPROFILE%\AppData\Local\ondonto-price-desktop
set SHORTCUT_DIR=%USERPROFILE%\Desktop
set STARTMENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
echo SUCESSO: Diretorios criados

REM Copiar arquivos
echo [4/5] Copiando arquivos...
copy "main.py" "%INSTALL_DIR%\" >nul
if exist "requirements.txt" copy "requirements.txt" "%INSTALL_DIR%\" >nul
echo SUCESSO: Arquivos copiados

REM Criar script de execução
echo [5/5] Criando atalhos...
(
echo @echo off
echo cd /d "%INSTALL_DIR%"
echo python main.py %%*
) > "%INSTALL_DIR%\run.bat"

REM Criar atalho no Desktop
echo Set oWS = WScript.CreateObject^("WScript.Shell"^) > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%SHORTCUT_DIR%\Sistema Comparacao Precos.lnk" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut^(sLinkFile^) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%INSTALL_DIR%\run.bat" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "Sistema de Comparacao de Precos - Odontopediatria" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"
cscript //nologo "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"

REM Criar atalho no Menu Iniciar
echo Set oWS = WScript.CreateObject^("WScript.Shell"^) > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%STARTMENU_DIR%\Sistema Comparacao Precos.lnk" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut^(sLinkFile^) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%INSTALL_DIR%\run.bat" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "Sistema de Comparacao de Precos - Odontopediatria" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"
cscript //nologo "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"

echo SUCESSO: Atalhos criados

echo.
echo ===============================================
echo INSTALACAO CONCLUIDA COM SUCESSO!
echo ===============================================
echo.
echo O aplicativo foi instalado em: %INSTALL_DIR%
echo.
echo Para executar:
echo   - Use o atalho na area de trabalho
echo   - Ou procure no menu Iniciar
echo   - Ou execute: %INSTALL_DIR%\run.bat
echo.
echo Para desinstalar:
echo   1. Delete a pasta: %INSTALL_DIR%
echo   2. Delete os atalhos criados
echo.

REM Perguntar se quer executar agora
set /p RUN_NOW="Deseja executar o aplicativo agora? (S/N): "
if /i "%RUN_NOW%"=="S" (
    echo.
    echo Iniciando o Sistema de Comparacao de Precos...
    start "" "%INSTALL_DIR%\run.bat"
)

echo.
echo Pressione qualquer tecla para sair...
pause >nul
