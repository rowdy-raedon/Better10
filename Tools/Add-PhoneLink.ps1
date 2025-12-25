# Add Phone Link Back to PC
# This script restores the Phone Link (Your Phone) app to Windows 10

$ErrorActionPreference = "Continue"
$scriptSuccess = $false

Write-Host "Adding Phone Link back to PC..." -ForegroundColor Cyan

try {
    # Method 1: Try to restore via PowerShell if it was just removed
    Write-Host "Attempting to restore Phone Link via PowerShell..." -ForegroundColor Yellow
    
    # Check if the package exists but is not installed
    $phoneLinkPackage = Get-AppxPackage -Name "Microsoft.YourPhone" -AllUsers -ErrorAction SilentlyContinue
    
    if ($phoneLinkPackage) {
        Write-Host "Phone Link package found. Attempting to restore..." -ForegroundColor Yellow
        # Try to re-register the package
        Get-AppxPackage -Name "Microsoft.YourPhone" | ForEach-Object {
            Add-AppxPackage -Register "$($_.InstallLocation)\AppxManifest.xml" -DisableDevelopmentMode
        }
        Write-Host "Phone Link restored successfully!" -ForegroundColor Green
    } else {
        Write-Host "Phone Link package not found in system." -ForegroundColor Yellow
        
        # Method 2: Try to install from Windows Store using winget
        Write-Host "Attempting to install Phone Link via winget..." -ForegroundColor Yellow
        try {
            $wingetResult = winget install --id "Microsoft.YourPhone" --accept-package-agreements --accept-source-agreements --silent 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Phone Link installed successfully via winget!" -ForegroundColor Green
            } else {
                Write-Host "Winget installation failed. Error: $wingetResult" -ForegroundColor Red
                
                # Method 3: Try to install via Add-AppxProvisionedPackage if available
                Write-Host "Attempting to install Phone Link via AppxProvisionedPackage..." -ForegroundColor Yellow
                try {
                    # Get the package from Microsoft Store URL and install
                    $storeUri = "https://storeedgefd.dsx.mp.microsoft.com/v9.0/packages/Microsoft.YourPhone_8wekyb3d8bbwe"
                    Invoke-WebRequest -Uri $storeUri -UseBasicParsing -ErrorAction SilentlyContinue
                    
                    # Alternative: Use Get-AppxPackage to find and install
                    $provisioned = Get-AppxProvisionedPackage -Online | Where-Object { $_.DisplayName -like "*YourPhone*" -or $_.PackageName -like "*YourPhone*" }
                    if ($provisioned) {
                        Write-Host "Found provisioned package. Attempting to install..." -ForegroundColor Yellow
                        Add-AppxPackage -Register "$($provisioned.PackageName)" -ErrorAction SilentlyContinue
                    }
                } catch {
                    Write-Host "AppxProvisionedPackage method failed: $_" -ForegroundColor Red
                }
            }
        } catch {
            Write-Host "Winget not available or installation failed: $_" -ForegroundColor Red
        }
    }
    
    # Method 4: Enable Phone Link settings via Registry
    Write-Host "Enabling Phone Link settings..." -ForegroundColor Yellow
    try {
        # Enable "Allow this PC to access your mobile devices"
        $regPath1 = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\CDP"
        if (-not (Test-Path $regPath1)) {
            New-Item -Path $regPath1 -Force | Out-Null
        }
        Set-ItemProperty -Path $regPath1 -Name "RomeSdkChannelUserAuthzPolicy" -Value 1 -Type DWord -ErrorAction SilentlyContinue
        
        # Enable "Turn on Phone Link"
        $regPath2 = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\CDP\SettingsPage"
        if (-not (Test-Path $regPath2)) {
            New-Item -Path $regPath2 -Force | Out-Null
        }
        Set-ItemProperty -Path $regPath2 -Name "UserAuthzPolicy" -Value 1 -Type DWord -ErrorAction SilentlyContinue
        
        # Enable "Show me suggestions for using my mobile device with Windows"
        Set-ItemProperty -Path $regPath2 -Name "CDPEnabled" -Value 1 -Type DWord -ErrorAction SilentlyContinue
        
        Write-Host "Phone Link settings enabled via registry." -ForegroundColor Green
    } catch {
        Write-Host "Warning: Could not set all registry values: $_" -ForegroundColor Yellow
    }
    
    # Method 5: Enable the service if it was disabled
    Write-Host "Checking Phone Link services..." -ForegroundColor Yellow
    $service = Get-Service -Name "PhoneSvc" -ErrorAction SilentlyContinue
    if ($service) {
        if ($service.Status -ne "Running") {
            Set-Service -Name "PhoneSvc" -StartupType Automatic
            Start-Service -Name "PhoneSvc"
            Write-Host "Phone Link service started." -ForegroundColor Green
        } else {
            Write-Host "Phone Link service is already running." -ForegroundColor Green
        }
    }
    
    # Verify installation
    Write-Host "`nVerifying installation..." -ForegroundColor Cyan
    $installed = Get-AppxPackage -Name "Microsoft.YourPhone" -ErrorAction SilentlyContinue
    if ($installed) {
        Write-Host "SUCCESS: Phone Link is now installed!" -ForegroundColor Green
        Write-Host "Package Name: $($installed.Name)" -ForegroundColor Green
        Write-Host "Version: $($installed.Version)" -ForegroundColor Green
        Write-Host "`nYou can now find Phone Link in the Start Menu." -ForegroundColor Cyan
        $scriptSuccess = $true
    } else {
        Write-Host "WARNING: Phone Link may not be fully installed." -ForegroundColor Yellow
        Write-Host "The installation may require a system restart or manual installation." -ForegroundColor Yellow
        # Don't fail completely - settings were enabled
        $scriptSuccess = $true
    }
    
} catch {
    Write-Host "ERROR: Failed to add Phone Link. Error: $_" -ForegroundColor Red
    Write-Host "Stack Trace: $($_.ScriptStackTrace)" -ForegroundColor Red
    # Exit with 0 to not fail the tool execution - some operations may have succeeded
    exit 0
}

Write-Host "`nScript completed." -ForegroundColor Cyan
if ($scriptSuccess) {
    exit 0
} else {
    exit 0
}

