@echo off
REM Script to translate the game by running various scripts and commands
REM Usage: translate_game.cmd "orig_dir" "clean_dir" "work_dir" "translation_dir" "nsis_dir"

REM Check if all 5 parameters are provided
if "%~5"=="" (
    echo Error: Missing parameters
    echo Usage: %0 "orig_dir" "clean_dir" "work_dir" "translation_dir" "nsis_dir"
    echo   orig_dir        - Directory containing original game files
    echo   clean_dir       - Directory containing clean game files
    echo   work_dir        - Directory containing work files
    echo   translation_dir - Directory containing translation files
    echo   nsis_dir        - Directory containing NSIS files
    exit /b 1
)

REM Set variables from command line parameters
set "ORIG_DIR=%~1"
set "CLEAN_DIR=%~2"
set "WORK_DIR=%~3"
set "TRANSLATION_DIR=%~4"
set "NSIS_DIR=%~5"

REM Display the parameters for confirmation
echo ========================================
echo Game Translation Script
echo ========================================
echo Original Directory:    %ORIG_DIR%
echo Clean Directory:       %CLEAN_DIR%
echo Work Directory:        %WORK_DIR%
echo Translation Directory: %TRANSLATION_DIR%
echo NSIS Directory:        %NSIS_DIR%
echo ========================================

REM Validate that directories exist
if not exist "%ORIG_DIR%" (
    echo Error: Original directory does not exist: %ORIG_DIR%
    exit /b 1
)

if not exist "%CLEAN_DIR%" (
    echo Error: Clean directory does not exist: %CLEAN_DIR%
    exit /b 1
) 

if not exist "%WORK_DIR%" (
    echo Error: Work directory does not exist: %WORK_DIR%
    exit /b 1
)
REM Create translation directory if it doesn't exist
if not exist "%TRANSLATION_DIR%" (
    echo Error: Translation directory does not exist: %TRANSLATION_DIR%
    exit /b 1
)

REM Validate that NSIS directory exists
if not exist "%NSIS_DIR%" (
    echo Error: NSIS directory does not exist: %NSIS_DIR%
    exit /b 1
) 

echo.
echo Starting game translation process...
echo.


echo.
echo ========================================
echo MANUAL STEP REQUIRED
echo ========================================
echo Please perform the following steps:
echo 1. Import the clean game into WinAGI from: %CLEAN_DIR%
echo 2. Make sure all override changes are applied, including:
echo    - Pictures
echo    - Views
echo    - Logic files
echo    - Any other custom resources
echo 3. Save your changes in WinAGI
echo.
echo Press any key to continue once you have completed these steps...
pause >nul
echo.
echo Continuing with automated process...
echo.


REM Clean work directory (fail on error) without PowerShell (avoid quoting issues)
echo Cleaning work directory: %WORK_DIR%
if not exist "%WORK_DIR%" (
    echo ERROR: Work directory missing: %WORK_DIR%
    exit /b 1
)

pushd "%WORK_DIR%" >nul 2>&1 || (echo ERROR: Cannot enter %WORK_DIR% & exit /b 1)

REM Delete files first
for /f "delims=" %%F in ('dir /a:-d /b 2^>nul') do (
    del /f /q "%%F" >nul 2>&1 || (echo ERROR deleting file %%F & popd & exit /b 1)
)

REM Delete directories
for /f "delims=" %%D in ('dir /ad /b 2^>nul') do (
    rd /s /q "%%D" >nul 2>&1 || (echo ERROR deleting directory %%D & popd & exit /b 1)
)

popd >nul 2>&1
echo Work directory cleaned.
pause
xcopy "%CLEAN_DIR%\*DIR" "%WORK_DIR%\" /Y
xcopy "%CLEAN_DIR%\VOL.*" "%WORK_DIR%\" /Y
xcopy "%CLEAN_DIR%\WORDS.TOK" "%WORK_DIR%\" /Y
xcopy "%CLEAN_DIR%\OBJECT" "%WORK_DIR%\" /Y
xcopy "%CLEAN_DIR%\src\*" "%WORK_DIR%\src\" /Y
xcopy "%CLEAN_DIR%\*.wag" "%WORK_DIR%\"  /Y

echo ========================================
echo COMPILE STEP REQUIRED
echo ========================================
echo Please perform the following steps:
echo 1. Open WinAGI and create/open the project in: %WORK_DIR%
echo 2. Make sure all resources are loaded properly. Remove and import new resources.
echo 3. Compile the game to generate updated VOL files
echo 4. Save the compiled game files
echo.
echo Press any key to continue once you have compiled the game...
pause >nul
echo.
echo Continuing with automated process...
echo.

python.exe .\tools\messages_import.py "%WORK_DIR%\src" "%TRANSLATION_DIR%"
if %ERRORLEVEL% neq 0 (
    echo ERROR: messages_import.py failed
    exit /b 1
)

python.exe .\tools\object_import.py "%WORK_DIR%" "%TRANSLATION_DIR%"
if %ERRORLEVEL% neq 0 (
    echo ERROR: object_import.py failed
    exit /b 1
)

python.exe .\tools\words_import.py "%WORK_DIR%" "%TRANSLATION_DIR%"
if %ERRORLEVEL% neq 0 (
    echo ERROR: words_import.py failed
    exit /b 1
)
xcopy "%NSIS_DIR%\agi-font-dos.bin" "%WORK_DIR%\" /Y

python.exe .\tools\apply_inventory_descriptions_batch.py "%WORK_DIR%" --file "%TRANSLATION_DIR%\inventory_heb.txt"
if %ERRORLEVEL% neq 0 (
     echo ERROR: apply_inventory_descriptions_batch.py failed
     exit /b 1
)


echo ========================================
echo COMPILE STEP REQUIRED
echo ========================================
echo Please perform the following steps:
echo 1. Open WinAGI and create/open the project in: %WORK_DIR%
echo 2. Compile the game to generate updated game files
echo.
echo Press any key to continue once you have compiled the game...
pause >nul
echo.
echo Continuing with automated process...
echo.

REM Check if uninstaller exists in original directory
if exist "%ORIG_DIR%\*uninstaller.exe" (
    echo ========================================
    echo UNINSTALLER DETECTED
    echo ========================================
    echo Found uninstaller in original directory: %ORIG_DIR%
    echo Please uninstall the old patch before creating a new one.
    echo.
    echo Starting uninstaller...
    for %%f in ("%ORIG_DIR%\*uninstaller.exe") do (
        echo Executing: %%f
        start /wait "" "%%f"
    )
    echo.
    echo Please complete the uninstallation process.
    echo Press any key to continue once uninstallation is complete...
    pause >nul
    echo.
    echo Continuing with patch creation...
    echo.
)

call .\tools\create_patches.cmd "%ORIG_DIR%" "%WORK_DIR%" "%NSIS_DIR%"
echo Copy the MD5 value below for AGI detection table:
powershell -Command "(Get-FileHash -Algorithm MD5 '%WORK_DIR%\LOGDIR').Hash.ToLower()"