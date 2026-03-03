# Forcefully stop all Python and Jan processes
$processes = @("python", "Jan")

foreach ($name in $processes) {
    $proc = Get-Process -Name $name -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Name $name -Force
        Write-Host "Terminated all $name processes." -ForegroundColor Cyan
    }
}
Stop-Process -Name "python", "Jan" -Force -ErrorAction SilentlyContinue
Write-Host "System cleared. You can now restart the Dorimon Launcher." -ForegroundColor Green