# Auto-deploy script for Windows
# Run with Task Scheduler every 5 minutes

$ProjectDir = "C:\Users\vip88\Desktop\ThaiWord"  # Change this
$LogFile = "$ProjectDir\deploy.log"

function Log($message) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $message" | Out-File -FilePath $LogFile -Append
}

try {
    Set-Location $ProjectDir

    # Fetch latest changes
    git fetch origin main 2>$null

    # Check if there are new commits
    $local = git rev-parse HEAD
    $remote = git rev-parse origin/main

    if ($local -ne $remote) {
        Log "New changes detected, deploying..."

        # Pull latest code
        git pull origin main

        # Install dependencies
        & ".\venv\Scripts\Activate.ps1"
        pip install -r requirements.txt

        # Restart service (kill existing and start new)
        Get-Process python -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -like "*run.py*"
        } | Stop-Process -Force

        Start-Process -FilePath "python" -ArgumentList "run.py" -WorkingDirectory $ProjectDir -WindowStyle Hidden

        Log "Deployment completed"
    } else {
        Log "No changes"
    }
} catch {
    Log "Error: $_"
}
