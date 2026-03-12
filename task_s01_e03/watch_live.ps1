param(
  [string]$SessionID = "",
  [string]$HostName = "azyl.ag3nts.org",
  [string]$UserName = "agent16805",
  [int]$Port = 5022
)

$logPath = "/home/a/agent16805/.pm2/logs/task-s01-e03-out.log"
$remoteCommand = "tail -n 0 -F $logPath"

Write-Host "Watching live conversation log from $UserName@$HostName`:$Port"
if ($SessionID) {
  Write-Host "Session filter: $SessionID"
}
Write-Host "Press Ctrl+C to stop.`n"

ssh "$UserName@$HostName" -p $Port $remoteCommand | ForEach-Object {
  $line = $_.Trim()
  if (-not $line) {
    return
  }

  try {
    $entry = $line | ConvertFrom-Json
  } catch {
    Write-Host $line
    return
  }

  if ($SessionID -and $entry.sessionID -ne $SessionID) {
    return
  }

  $timestamp = $entry.at
  $session = $entry.sessionID

  if ($null -ne $entry.msg) {
    Write-Host "[$timestamp] [$session] USER: $($entry.msg)" -ForegroundColor Yellow
    return
  }

  if ($null -ne $entry.reply) {
    Write-Host "[$timestamp] [$session] BOT : $($entry.reply)" -ForegroundColor Cyan
    return
  }

  Write-Host $line
}
