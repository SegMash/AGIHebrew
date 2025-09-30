@echo off
REM Script to create patches by comparing clean and work directories
REM Usage: create_patches.cmd "clean_dir" "work_dir" "nsis_dir"

REM Check if all 3 parameters are provided
if "%~3"=="" (
    echo Error: Missing parameters
    echo Usage: %0 "clean_dir" "work_dir" "nsis_dir"
    echo   clean_dir  - Directory containing clean game files
    echo   work_dir   - Directory containing modified game files
    echo   nsis_dir   - Directory for NSIS files and patches
    exit /b 1
)

REM Set variables from command line parameters - use pushd/popd for better path handling
pushd "%~1" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "CLEAN_DIR=%CD%"
    popd
) else (
    echo Error: Cannot access clean directory: %~1
    exit /b 1
)

pushd "%~2" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "WORK_DIR=%CD%"
    popd
) else (
    echo Error: Cannot access work directory: %~2
    exit /b 1
)

pushd "%~3" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "NSIS_DIR=%CD%"
    popd
) else (
    echo Error: Cannot access NSIS directory: %~3
    exit /b 1
)

REM Display the parameters for confirmation
echo ========================================
echo Patch Creation Script
echo ========================================
echo Clean Directory: %CLEAN_DIR%
echo Work Directory:  %WORK_DIR%
echo NSIS Directory:  %NSIS_DIR%
echo ========================================

echo.
echo Creating patches...
echo.

GenPat.exe "%CLEAN_DIR%\VOL.0" "%WORK_DIR%\VOL.0" "%NSIS_DIR%\VOL.0.patch" /r
GenPat.exe "%CLEAN_DIR%\OBJECT" "%WORK_DIR%\OBJECT" "%NSIS_DIR%\OBJECT.patch" /r
GenPat.exe "%CLEAN_DIR%\LOGDIR" "%WORK_DIR%\LOGDIR" "%NSIS_DIR%\LOGDIR.patch" /r
GenPat.exe "%CLEAN_DIR%\SNDDIR" "%WORK_DIR%\SNDDIR" "%NSIS_DIR%\SNDDIR.patch" /r
GenPat.exe "%CLEAN_DIR%\PICDIR" "%WORK_DIR%\PICDIR" "%NSIS_DIR%\PICDIR.patch" /r 
GenPat.exe "%CLEAN_DIR%\WORDS.TOK" "%WORK_DIR%\WORDS.TOK" "%NSIS_DIR%\WORDS.TOK.patch" /r
GenPat.exe "%CLEAN_DIR%\VIEWDIR" "%WORK_DIR%\VIEWDIR" "%NSIS_DIR%\VIEWDIR.patch" /r
xcopy "%WORK_DIR%\WORDS.TOK.EXTENDED" "%NSIS_DIR%\" /Y
makensis.exe "%NSIS_DIR%\installer.nsi"

echo.
echo Patches created successfully!
echo Check the %NSIS_DIR% directory for patch files.