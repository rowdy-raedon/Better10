# Better10 - Quick Start Guide

## Prerequisites Check

Before running Better10, ensure you have:

1. ✅ **Windows 10** (64-bit)
2. ✅ **Python 3.10+** installed
3. ✅ **Administrator access**
4. ✅ **Winget** installed (usually pre-installed on Windows 10 1809+)

## Quick Installation

1. **Install Python dependencies:**
   ```powershell
   pip install PyQt5
   ```

2. **Verify winget is available:**
   ```powershell
   winget --version
   ```
   If not installed, get it from: https://aka.ms/getwinget

## Running Better10

### Method 1: Right-Click Run as Administrator
1. Right-click `better10.py`
2. Select **"Run as administrator"**
3. Click "Yes" on the UAC prompt

### Method 2: PowerShell (Recommended)
1. Right-click **Start** button → **Windows PowerShell (Admin)**
2. Navigate to the Better10 folder:
   ```powershell
   cd C:\Users\Raedon\Desktop\Better10
   ```
3. Run the application:
   ```powershell
   python better10.py
   ```

## First-Time Usage

1. **Check Admin Status**: The app will warn you if not running as admin
2. **Select Operations**: 
   - Go through each tab
   - Check boxes for operations you want
   - Use "Select All" / "Deselect All" buttons
3. **Review Selections**: Check the Logs tab to see what will happen
4. **Execute**: Click "Execute All Selected Operations"
5. **Monitor**: Watch the Logs tab for real-time progress

## Recommended First Run

For a safe first run, try:

1. **Application Installer**: Select 1-2 apps (e.g., Chrome, 7-Zip)
2. **Bloatware Removal**: Select 2-3 non-critical apps (e.g., Feedback Hub, Get Started)
3. **Privacy & Telemetry**: Select all (these are generally safe)
4. **Security Components**: ⚠️ **SKIP** on first run - these are dangerous

## Common Issues

### "Administrator privileges required"
- Right-click and run as administrator
- Or run PowerShell as admin first

### "Winget not found"
- Install from Microsoft Store: https://aka.ms/getwinget
- Or download from: https://github.com/microsoft/winget-cli/releases

### Applications won't install
- Check internet connection
- Verify winget works: `winget search chrome`
- Some apps may need manual installation

### PowerShell errors
- Run: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`
- In PowerShell as admin

## Safety Tips

- ✅ **Backup your system** before major changes
- ✅ **Test on a non-production system** first
- ✅ **Start with small selections** to verify functionality
- ⚠️ **Never disable Defender** without alternative antivirus
- ⚠️ **Be cautious** removing Edge (affects Windows Update)

## Need Help?

Check the main README.md for detailed documentation and troubleshooting.

