@echo off
cd /d "%~dp0"

"%~dp0venv\Scripts\python.exe" "%~dp0scraperemail.py" >> "%~dp0scraper_log.txt" 2>&1