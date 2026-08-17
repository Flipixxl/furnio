# Останавливает Cloudflare-туннель (сайт перестаёт быть виден из интернета).
# Flask-сервер продолжает работать для локальной сети.

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "Cloudflare Tunnel остановлен. Сайт больше не доступен из интернета." -ForegroundColor Yellow

if (Test-Path (Join-Path $root "public_url.txt")) {
    Remove-Item (Join-Path $root "public_url.txt")
    Write-Host "Ссылка public_url.txt удалена." -ForegroundColor Gray
}

Write-Host "Для повторного запуска выполните: .\start_public.ps1" -ForegroundColor Gray