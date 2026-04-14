@echo off
chcp 65001 > nul
call C:\Users\owner\Documents\project\2026-03-PDFagent\venv\Scripts\activate.bat
doskey pa-run=python C:\Users\owner\Documents\project\2026-03-PDFagent\main.py
doskey pa-list=python C:\Users\owner\Documents\project\2026-03-PDFagent\tools\list_papers.py
doskey pa-init=python C:\Users\owner\Documents\project\2026-03-PDFagent\tools\init.py
doskey pa-redo=python C:\Users\owner\Documents\project\2026-03-PDFagent\tools\rerun.py
doskey pa-migrate=python C:\Users\owner\Documents\project\2026-03-PDFagent\tools\migrate.py
doskey pa-exit=deactivate
echo.
echo Ready. Available commands:
echo   pa-init    - initialize folder structure
echo   pa-run     - process papers
echo   pa-list    - list records
echo   pa-redo    - rerun a paper
echo   pa-migrate - migrate old output to date folders
echo   pa-exit    - exit environment
echo.
cmd /k
