# Auto Git Add + Commit + Push
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$commitMessage = "Auto-push at $timestamp"

Write-Host "Adding changes..."
git add .

Write-Host "Committing..."
git commit -m "$commitMessage"

Write-Host "Pushing to origin/main..."
git push origin main

Write-Host "Done!"
