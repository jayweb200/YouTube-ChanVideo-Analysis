@echo off
echo Starting HTTP server for YouTube Analysis Dashboard...
echo.
echo Please keep this window open while using the dashboard.
echo When you're done, close this window to stop the server.
echo.
echo Dashboard will be available at: http://localhost:8000/analysis-dashboard.html
echo.
python -m http.server 8000
