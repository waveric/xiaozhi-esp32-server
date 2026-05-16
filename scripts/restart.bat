@echo off
REM ============================================================
REM xiaozhi-esp32-server Restart Script
REM Supports configuration rollback on failure
REM ============================================================

setlocal enabledelayedexpansion

REM 参数
set CONFIG_FILE=%1
set BASE_DIR=%~dp0..
set DATA_DIR=%BASE_DIR%\main\xiaozhi-server\data
set LOG_FILE=%DATA_DIR%\restart.log
set PID_FILE=%DATA_DIR%\xiaozhi.pid

REM 记录日志
echo [%date% %time%] Restart script started >> "%LOG_FILE%"
echo [%date% %time%] Config file: %CONFIG_FILE% >> "%LOG_FILE%"

REM 检查配置文件是否存在
if not "%CONFIG_FILE%"=="" (
    if exist "%DATA_DIR%\configs\%CONFIG_FILE%" (
        REM 备份当前激活配置
        if exist "%DATA_DIR%\.config.yaml" (
            echo [%date% %time%] Backing up current config >> "%LOG_FILE%"
            copy /Y "%DATA_DIR%\.config.yaml" "%DATA_DIR%\.config.yaml.bak" >> "%LOG_FILE%" 2>&1
        )

        REM 复制新配置
        echo [%date% %time%] Copying new config: %CONFIG_FILE% >> "%LOG_FILE%"
        copy /Y "%DATA_DIR%\configs\%CONFIG_FILE%" "%DATA_DIR%\.config.yaml" >> "%LOG_FILE%" 2>&1
    ) else (
        echo [%date% %time%] ERROR: Config file not found: %CONFIG_FILE% >> "%LOG_FILE%"
        echo {"success": false, "error": "Config file not found"} > "%DATA_DIR%\restart_result.json"
        exit /b 1
    )
)

REM 获取当前运行的 python 进程 PID（查找 app.py）
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr "PID:"') do (
    wmic process where "ProcessId=%%i and CommandLine like '%%app.py%%'" get ProcessId 2>nul | findstr "%%i" >nul
    if !errorlevel!==0 (
        set CURRENT_PID=%%i
        echo [%date% %time%] Found running xiaozhi process: PID %%i >> "%LOG_FILE%"
    )
)

REM 停止当前进程
if defined CURRENT_PID (
    echo [%date% %time%] Stopping process PID !CURRENT_PID! >> "%LOG_FILE%"
    taskkill /PID !CURRENT_PID! /F >> "%LOG_FILE%" 2>&1
    timeout /t 2 /nobreak >nul
)

REM 保存 PID 到文件（新启动时会更新）
echo starting > "%PID_FILE%"

REM 启动新进程
cd /d "%BASE_DIR%\main\xiaozhi-server"
echo [%date% %time%] Starting new process >> "%LOG_FILE%"
start "xiaozhi-esp32-server" /min python app.py

REM 等待启动
set WAIT_COUNT=0
:wait_loop
timeout /t 1 /nobreak >nul
set /a WAIT_COUNT+=1

REM 检查新进程是否启动成功
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr "PID:"') do (
    wmic process where "ProcessId=%%i and CommandLine like '%%app.py%%'" get ProcessId 2>nul | findstr "%%i" >nul
    if !errorlevel!==0 (
        set NEW_PID=%%i
    )
)

if defined NEW_PID (
    if not "!NEW_PID!"=="!CURRENT_PID!" (
        echo !NEW_PID! > "%PID_FILE%"
        echo [%date% %time%] New process started: PID !NEW_PID! >> "%LOG_FILE%"
        goto :success
    )
)

if %WAIT_COUNT% LSS 15 goto :wait_loop

REM 启动失败，回滚
echo [%date% %time%] ERROR: Failed to start new process >> "%LOG_FILE%"

REM 回滚配置
if exist "%DATA_DIR%\.config.yaml.bak" (
    echo [%date% %time%] Rolling back config >> "%LOG_FILE%"
    copy /Y "%DATA_DIR%\.config.yaml.bak" "%DATA_DIR%\.config.yaml" >> "%LOG_FILE%" 2>&1

    REM 尝试使用备份配置启动
    start "xiaozhi-esp32-server" /min python app.py
)

echo {"success": false, "error": "Failed to start new process", "rollback": true} > "%DATA_DIR%\restart_result.json"
exit /b 1

:success
echo [%date% %time%] Restart successful >> "%LOG_FILE%"
echo {"success": true, "new_pid": !NEW_PID!} > "%DATA_DIR%\restart_result.json"
exit /b 0
