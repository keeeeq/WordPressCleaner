@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo   WordPress 数据清洗工具 - 一键启动
echo ============================================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 查找 XML 文件
echo [提示] 请将 WordPress 导出的 XML 文件拖放到此窗口，然后按回车:
echo        （或直接按回车，将在当前目录搜索 .xml 文件）
echo.

set /p INPUT_FILE=输入文件路径: 

if "%INPUT_FILE%"=="" (
    echo.
    echo [信息] 在当前目录搜索 XML 文件...
    for %%f in (*.xml) do (
        set INPUT_FILE=%%f
        goto :found
    )
    echo [错误] 当前目录未找到 XML 文件
    pause
    exit /b 1
)

:found
echo.
echo [信息] 开始处理: %INPUT_FILE%
echo.

REM 运行 Python 脚本
python "%~dp0wordpress_cleaner.py" "%INPUT_FILE%"

echo.
pause
