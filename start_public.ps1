# Скрипт для публикации Furnio в интернет через Cloudflare Tunnel.
# Запуск:  .\start_public.ps1
# Остановка: .\stop_public.ps1   (или Ctrl+C в этом окне)
#
# Ссылка появится в этом окне и будет сохранена в public_url.txt

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\python.exe"
$cloudflared = Join-Path $root "tools\cloudflared.exe"
$logOut = Join-Path $root "cloudflared.out.log"
$logErr = Join-Path $root "cloudflared.log"

if (-not (Test-Path $python))  { Write-Error "Не найден Python: $python"; exit 1 }
if (-not (Test-Path $cloudflared)) { Write-Error "Не найден cloudflared. Скачайте его с github.com/cloudflare/cloudflared в tools\cloudflared.exe"; exit 1 }

# 1. Запускаем Flask-сервер
$server = Get-Process python -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -like "*furniture_shop*" } |
    Select-Object -First 1
if (-not $server) {
    $server = Start-Process -FilePath $python -ArgumentList "app.py" `
        -WorkingDirectory $root -WindowStyle Hidden -PassThru
    Write-Host "Сервер Furnio запущен (PID $($server.Id))" -ForegroundColor Green
    Start-Sleep -Seconds 4
} else {
    Write-Host "Сервер Furnio уже запущен (PID $($server.Id))" -ForegroundColor Yellow
}

# 2. Проверяем, что сайт отвечает
try {
    Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -UseBasicParsing -TimeoutSec 8 | Out-Null
} catch {
    Write-Error "Сайт не отвечает на http://127.0.0.1:5000"; exit 1
}

# 3. Запускаем Cloudflare-туннель
Write-Host "Запускаю Cloudflare Tunnel... ссылка появится через ~10 секунд" -ForegroundColor Cyan
$proc = Start-Process -FilePath $cloudflared -ArgumentList "tunnel", "--url", "http://127.0.0.1:5000", "--no-autoupdate" `
    -WorkingDirectory $root -RedirectStandardOutput $logOut -RedirectStandardError $logErr -PassThru -WindowStyle Hidden

# 4. Ждём появления ссылки
$url = $null
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $logErr) {
        $content = Get-Content $logErr -Raw -ErrorAction SilentlyContinue
        if ($content -match "https://[a-z0-9-]+\.trycloudflare\.com") {
            $url = $Matches[0]
            break
        }
    }
    if ($proc.HasExited) {
        Write-Error "cloudflared завершился с ошибкой. Смотрите $logErr"; exit 1
    }
}

if (-not $url) {
    Write-Error "Не удалось получить ссылку. Смотрите $logErr"; exit 1
}

$url | Set-Content (Join-Path $root "public_url.txt")
Write-Host ""
Write-Host "  САЙТ В ИНТЕРНЕТЕ:" -ForegroundColor Green
Write-Host "  $url" -ForegroundColor Green -NoNewline
Write-Host "  (ссылка сохранена в public_url.txt)"
Write-Host ""
Write-Host "Раздавайте эту ссылку кому угодно — сайт доступен из любой точки мира." -ForegroundColor Cyan
Write-Host "Для остановки запустите .\stop_public.ps1" -ForegroundColor Gray