# Better10 - Windows 10 Post-Install Automation Tool

A comprehensive PyQt5 desktop application for automating post-installation tasks on Windows 10, including application installation, bloatware removal, privacy settings, and security component management.

## ⚠️ WARNING

**This application makes system-level changes that can significantly affect Windows security and functionality.**

- Disabling Windows Defender will reduce your system security
- Removing system components may affect Windows Update and other functions
- Registry modifications can impact system stability
- **Use at your own risk**

## Requirements

- **Operating System**: Windows 10 (64-bit)
- **Python**: 3.10 or higher
- **Administrator Privileges**: Required for most operations
- **Winget**: Should be installed (comes with Windows 10 1809+ or can be installed separately)

## Installation

### Step 1: Install Python 3.10+

1. Download Python 3.10+ from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Verify installation:
   ```powershell
   python --version
   ```

### Step 2: Install Required Packages

Open PowerShell or Command Prompt **as Administrator** and run:

```powershell
pip install -r requirements.txt
```

Or install PyQt5 directly:

```powershell
pip install PyQt5
```

### Step 3: Verify Winget Installation

Winget should be available on Windows 10 1809+. To check:

```powershell
winget --version
```

If winget is not available, install it from the [Microsoft Store](https://aka.ms/getwinget) or download the latest release from [GitHub](https://github.com/microsoft/winget-cli/releases).

## Usage

### Running the Application

1. **Right-click** on `better10.py` and select **"Run as administrator"**
   - Or open PowerShell as Administrator and run:
     ```powershell
     python better10.py
     ```

2. The application will check for administrator privileges on startup
   - If not running as admin, you'll see a warning
   - Many operations require admin rights to function properly

### Application Features

#### 1. Application Installer Tab
- Select applications to install via winget
- All installations run silently
- Installations execute sequentially to avoid conflicts
- Includes popular applications like Chrome, Firefox, VSCode, 7-Zip, etc.

#### 2. Bloatware Removal Tab
- Remove default Windows apps (Xbox, OneDrive, Cortana, etc.)
- Uses PowerShell commands with error handling
- Safe removal of non-critical components

#### 3. Privacy & Telemetry Tab
- Disable Windows telemetry and data collection
- Modify registry settings for privacy
- Disable advertising ID, location tracking, activity history, etc.

#### 4. Security Components Tab
- **⚠️ CRITICAL**: Disable Windows Defender (requires alternative antivirus)
- Remove Microsoft Edge (may affect Windows Update)
- Disable Windows Firewall (NOT RECOMMENDED)

#### 5. Logs / Status Tab
- Real-time operation logs
- Color-coded messages (Info, Success, Warning, Error)
- Timestamped entries

### Workflow

1. Navigate through tabs and select desired operations using checkboxes
2. Review your selections
3. Click **"Execute All Selected Operations"** button
4. Confirm the operation
5. Monitor progress in the Logs tab
6. Wait for all operations to complete

## Technical Details

### System Operations

The application uses three main methods for system changes:

1. **Winget**: For installing/uninstalling applications
   - Silent installations
   - Package management

2. **PowerShell**: For removing apps and disabling services
   - AppxPackage removal
   - Service management
   - System configuration

3. **Registry**: For privacy and security settings
   - HKEY_LOCAL_MACHINE for system-wide settings
   - HKEY_CURRENT_USER for user-specific settings
   - REG_DWORD for integer values
   - REG_SZ for string values

### Administrator Privileges

The application checks for admin privileges using `ctypes.windll.shell32.IsUserAnAdmin()`. Most operations require administrator rights to modify system settings.

### Error Handling

- All operations include try-catch error handling
- Failed operations are logged with error messages
- Operations continue even if individual steps fail
- Timeout protection for long-running operations (5-10 minutes)

## Troubleshooting

### "Administrator privileges required" error
- Right-click the Python script and select "Run as administrator"
- Or run PowerShell/Command Prompt as admin first

### Winget not found
- Install winget from Microsoft Store or GitHub
- Ensure you're on Windows 10 1809 or later

### Applications fail to install
- Check internet connection
- Verify winget is working: `winget search chrome`
- Some applications may require manual installation

### Registry changes not taking effect
- Restart your computer
- Some changes require a reboot to apply
- Verify you're running as administrator

### PowerShell execution errors
- Check PowerShell execution policy: `Get-ExecutionPolicy`
- May need to run: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

## Safety Notes

- **Backup your system** before running this tool
- Test on a non-production system first
- Some operations cannot be easily undone
- Disabling Windows Defender without alternative protection is dangerous
- Removing Edge may affect Windows Update functionality

## Customization

You can modify the application lists in the code:

- **Applications**: Edit `self.apps` dictionary in `ApplicationInstallerTab`
- **Bloatware**: Edit `self.bloatware` dictionary in `BloatwareRemovalTab`
- **Privacy Settings**: Edit `self.privacy_settings` dictionary in `PrivacyTelemetryTab`
- **Security Operations**: Edit `self.security_operations` dictionary in `SecurityComponentsTab`

## License

This tool is provided as-is for personal use. Use at your own risk.

## Support

For issues or questions:
1. Check the Logs tab for detailed error messages
2. Verify administrator privileges
3. Ensure all prerequisites are installed
4. Review PowerShell execution policy settings

## Disclaimer

This software is provided "as is" without warranty of any kind. The authors are not responsible for any damage or data loss resulting from the use of this tool. Users are responsible for understanding the implications of disabling security features and removing system components.

