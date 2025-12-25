# Remove Microsoft Edge
# Based on Chris Titus Tech Winutil method
# Credit: Techie Jack
# Source: https://winutil.christitus.com/dev/tweaks/z--advanced-tweaks---caution/removeedge/

$ErrorActionPreference = "Continue"
$scriptSuccess = $false

Write-Host "Removing Microsoft Edge..." -ForegroundColor Cyan

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script requires administrator privileges." -ForegroundColor Red
    Write-Host "Please run PowerShell as administrator and try again." -ForegroundColor Yellow
    exit 1
}

try {
    # Stop Edge processes
    Write-Host "Stopping Microsoft Edge processes..." -ForegroundColor Yellow
    $msedgeProcess = Get-Process -Name "msedge" -ErrorAction SilentlyContinue
    $widgetsProcess = Get-Process -Name "widgets" -ErrorAction SilentlyContinue
    
    if ($msedgeProcess) {
        Stop-Process -Name "msedge" -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped msedge process." -ForegroundColor Green
    } else {
        Write-Host "msedge process is not running." -ForegroundColor Gray
    }
    
    if ($widgetsProcess) {
        Stop-Process -Name "widgets" -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped widgets process." -ForegroundColor Green
    } else {
        Write-Host "widgets process is not running." -ForegroundColor Gray
    }
    
    # Function to uninstall Edge components
    function Uninstall-Process {
        param (
            [Parameter(Mandatory = $true)]
            [string]$Key,
            [Parameter(Mandatory = $true)]
            [string]$Mode
        )

        Write-Host "Processing $Mode..." -ForegroundColor Yellow
        
        # Save original Nation setting
        $originalNation = [microsoft.win32.registry]::GetValue('HKEY_USERS\.DEFAULT\Control Panel\International\Geo', 'Nation', [Microsoft.Win32.RegistryValueKind]::String)
        
        # Set Nation to 68 (Ireland) temporarily to allow uninstallation
        [microsoft.win32.registry]::SetValue('HKEY_USERS\.DEFAULT\Control Panel\International\Geo', 'Nation', 68, [Microsoft.Win32.RegistryValueKind]::String) | Out-Null
        Write-Host "Temporarily changed region to allow uninstallation..." -ForegroundColor Gray

        # Handle IntegratedServicesRegionPolicySet.json ACL
        $fileName = "IntegratedServicesRegionPolicySet.json"
        $pathISRPS = [Environment]::SystemDirectory + "\" + $fileName
        $aclISRPSBackup = $null
        
        if (Test-Path -Path $pathISRPS) {
            try {
                $aclISRPS = Get-Acl -Path $pathISRPS
                $aclISRPSBackup = [System.Security.AccessControl.FileSecurity]::new()
                $aclISRPSBackup.SetSecurityDescriptorSddlForm($aclISRPS.Sddl)
                
                $admin = [System.Security.Principal.NTAccount]$(New-Object System.Security.Principal.SecurityIdentifier('S-1-5-32-544')).Translate([System.Security.Principal.NTAccount]).Value
                $aclISRPS.SetOwner($admin)
                $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($admin, 'FullControl', 'Allow')
                $aclISRPS.AddAccessRule($rule)
                Set-Acl -Path $pathISRPS -AclObject $aclISRPS

                Rename-Item -Path $pathISRPS -NewName ($fileName + '.bak') -Force
                Write-Host "Modified ACL for IntegratedServicesRegionPolicySet.json" -ForegroundColor Gray
            }
            catch {
                Write-Host "Warning: Failed to modify ACL for $pathISRPS : $_" -ForegroundColor Yellow
            }
        }

        # Get uninstall information from registry
        $baseKey = 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate'
        $registryPath = $baseKey + '\ClientState\' + $Key

        if (!(Test-Path -Path $registryPath)) {
            Write-Host "[$Mode] Registry key not found: $registryPath" -ForegroundColor Yellow
            return
        }

        # Remove experiment_control_labels property
        Remove-ItemProperty -Path $registryPath -Name "experiment_control_labels" -ErrorAction SilentlyContinue | Out-Null

        $uninstallString = (Get-ItemProperty -Path $registryPath -ErrorAction SilentlyContinue).UninstallString
        $uninstallArguments = (Get-ItemProperty -Path $registryPath -ErrorAction SilentlyContinue).UninstallArguments

        if ([string]::IsNullOrEmpty($uninstallString) -or [string]::IsNullOrEmpty($uninstallArguments)) {
            Write-Host "[$Mode] Cannot find uninstall methods" -ForegroundColor Yellow
            return
        }

        $uninstallArguments += " --force-uninstall --delete-profile"

        if (!(Test-Path -Path $uninstallString)) {
            Write-Host "[$Mode] setup.exe not found at: $uninstallString" -ForegroundColor Yellow
            return
        }
        
        Write-Host "[$Mode] Running uninstaller..." -ForegroundColor Yellow
        Start-Process -FilePath $uninstallString -ArgumentList $uninstallArguments -Wait -NoNewWindow

        # Restore ACL
        if ($aclISRPSBackup -and (Test-Path -Path ($pathISRPS + '.bak'))) {
            Rename-Item -Path ($pathISRPS + '.bak') -NewName $fileName -Force
            Set-Acl -Path $pathISRPS -AclObject $aclISRPSBackup
            Write-Host "Restored ACL for IntegratedServicesRegionPolicySet.json" -ForegroundColor Gray
        }

        # Restore original Nation setting
        [microsoft.win32.registry]::SetValue('HKEY_USERS\.DEFAULT\Control Panel\International\Geo', 'Nation', $originalNation, [Microsoft.Win32.RegistryValueKind]::String) | Out-Null
        Write-Host "Restored original region setting" -ForegroundColor Gray

        # Verify uninstallation
        if ((Get-ItemProperty -Path $baseKey -ErrorAction SilentlyContinue).IsEdgeStableUninstalled -eq 1) {
            Write-Host "[$Mode] Successfully uninstalled" -ForegroundColor Green
        }
    }

    # Function to uninstall Edge browser
    function Uninstall-Edge {
        Write-Host "`nUninstalling Microsoft Edge..." -ForegroundColor Cyan
        
        # Remove NoRemove property to allow uninstallation
        Remove-ItemProperty -Path "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Microsoft Edge" -Name "NoRemove" -ErrorAction SilentlyContinue | Out-Null
        
        # Allow uninstall in EdgeUpdateDev
        [microsoft.win32.registry]::SetValue("HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdateDev", "AllowUninstall", 1, [Microsoft.Win32.RegistryValueKind]::DWord) | Out-Null

        # Uninstall Edge Stable
        Uninstall-Process -Key '{56EB18F8-B008-4CBD-B6D2-8C97FE7E9062}' -Mode "Edge Stable"

        # Remove shortcuts
        Write-Host "Removing Edge shortcuts..." -ForegroundColor Yellow
        @( "$env:ProgramData\Microsoft\Windows\Start Menu\Programs",
           "$env:PUBLIC\Desktop",
           "$env:USERPROFILE\Desktop" ) | ForEach-Object {
            $shortcutPath = Join-Path -Path $_ -ChildPath "Microsoft Edge.lnk"
            if (Test-Path -Path $shortcutPath) {
                Remove-Item -Path $shortcutPath -Force -ErrorAction SilentlyContinue
                Write-Host "Removed shortcut: $shortcutPath" -ForegroundColor Gray
            }
        }
    }

    # Function to uninstall Edge Update
    function Uninstall-EdgeUpdate {
        Write-Host "`nUninstalling Microsoft Edge Update..." -ForegroundColor Cyan
        
        Remove-ItemProperty -Path "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Microsoft Edge Update" -Name "NoRemove" -ErrorAction SilentlyContinue | Out-Null

        $registryPath = 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate'
        if (!(Test-Path -Path $registryPath)) {
            Write-Host "Edge Update registry key not found" -ForegroundColor Yellow
            return
        }
        
        $uninstallCmdLine = (Get-ItemProperty -Path $registryPath -ErrorAction SilentlyContinue).UninstallCmdLine

        if ([string]::IsNullOrEmpty($uninstallCmdLine)) {
            Write-Host "Cannot find Edge Update uninstall method" -ForegroundColor Yellow
            return
        }

        Write-Host "Running Edge Update uninstaller..." -ForegroundColor Yellow
        Start-Process cmd.exe -ArgumentList "/c $uninstallCmdLine" -WindowStyle Hidden -Wait
        Write-Host "Edge Update uninstalled" -ForegroundColor Green
    }

    # Execute uninstallation
    Uninstall-Edge
    Uninstall-EdgeUpdate

    # Verify removal
    Write-Host "`nVerifying removal..." -ForegroundColor Cyan
    $edgeInstalled = Get-AppxPackage -Name "*MicrosoftEdge*" -ErrorAction SilentlyContinue
    $edgeUpdate = Get-ItemProperty -Path "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Microsoft Edge Update" -ErrorAction SilentlyContinue
    
    if (-not $edgeInstalled -and -not $edgeUpdate) {
        Write-Host "SUCCESS: Microsoft Edge has been removed!" -ForegroundColor Green
        $scriptSuccess = $true
    } else {
        Write-Host "WARNING: Some Edge components may still be present." -ForegroundColor Yellow
        Write-Host "A system restart may be required for complete removal." -ForegroundColor Yellow
        $scriptSuccess = $true
    }
    
} catch {
    Write-Host "ERROR: Failed to remove Microsoft Edge. Error: $_" -ForegroundColor Red
    Write-Host "Stack Trace: $($_.ScriptStackTrace)" -ForegroundColor Red
    exit 0
}

Write-Host "`nScript completed." -ForegroundColor Cyan
if ($scriptSuccess) {
    exit 0
} else {
    exit 0
}

