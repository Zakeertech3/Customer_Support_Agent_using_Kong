@echo off
setlocal enabledelayedexpansion

echo Starting Kong AI Gateway setup...

if "%GROQ_API_KEY%"=="" (
    echo Error: GROQ_API_KEY environment variable is not set
    exit /b 1
)

echo Starting Docker Compose services...
docker-compose up -d

echo Waiting for Kong to be ready...
set timeout=300
set counter=0

:wait_loop
curl -f http://localhost:8001/status >nul 2>&1
if %errorlevel% equ 0 goto kong_ready

if !counter! geq %timeout% (
    echo Timeout waiting for Kong to be ready
    exit /b 1
)

echo Kong is not ready yet. Waiting... (!counter!/%timeout%)
timeout /t 5 /nobreak >nul
set /a counter+=5
goto wait_loop

:kong_ready
echo Kong is ready!

echo Checking for deck CLI tool...
deck version >nul 2>&1
if %errorlevel% neq 0 (
    echo Please install deck CLI tool from: https://github.com/Kong/deck/releases
    echo Download deck_windows_amd64.tar.gz and extract deck.exe to your PATH
    exit /b 1
)

echo Applying Kong configuration...
deck sync --kong-addr http://localhost:8001 --state kong/kong.yml

echo Creating consumers for rate limiting...
curl -X POST http://localhost:8001/consumers --data "username=support-agent" --data "custom_id=support-agent-001"
curl -X POST http://localhost:8001/consumers/support-agent/key-auth --data "key=support-agent-key-123"

echo Verifying Kong setup...
echo Services:
curl -s http://localhost:8001/services

echo Routes:
curl -s http://localhost:8001/routes

echo Plugins:
curl -s http://localhost:8001/plugins

echo Kong AI Gateway setup completed successfully!
echo Kong Proxy: http://localhost:8000
echo Kong Admin: http://localhost:8001
echo Kong Manager: http://localhost:8002
echo ChromaDB: http://localhost:8003