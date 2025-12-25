#!/usr/bin/env python3
"""
Better10 - Windows 10 Post-Install Automation Tool
A PyQt5 application for automating post-installation tasks on Windows 10.

WARNING: This application makes system-level changes that can affect
Windows security and functionality. Use at your own risk.

Author: Generated for Windows 10 Post-Install Automation
Python Version: 3.10+
"""

import sys
import os
import subprocess
import winreg
import ctypes
from datetime import datetime
from typing import List, Dict, Tuple

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QCheckBox, QTextEdit, QLabel, QScrollArea,
    QMessageBox, QProgressBar, QShortcut
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor, QPalette, QKeySequence


class LogLevel:
    """Log level constants"""
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


class SystemOperations:
    """Handles all system-level operations"""
    
    @staticmethod
    def is_admin() -> bool:
        """Check if the application is running with administrator privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    @staticmethod
    def run_powershell(command: str, as_admin: bool = False) -> Tuple[bool, str, str]:
        """
        Execute a PowerShell command and return the result
        
        Args:
            command: PowerShell command to execute
            as_admin: Whether to run as administrator (requires elevation)
        
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        try:
            if as_admin:
                # Run PowerShell as administrator
                ps_command = f'powershell.exe -Command "Start-Process powershell -ArgumentList \\"-NoProfile -ExecutionPolicy Bypass -Command {command}\\" -Verb RunAs -Wait"'
                result = subprocess.run(
                    ps_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            else:
                # Run PowerShell normally
                ps_command = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "{command}"'
                result = subprocess.run(
                    ps_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out after 300 seconds"
        except Exception as e:
            return False, "", str(e)
    
    @staticmethod
    def run_winget(operation: str, package_id: str = None) -> Tuple[bool, str, str]:
        """
        Execute winget command
        
        Args:
            operation: 'install', 'uninstall', 'list', etc.
            package_id: Package identifier for install/uninstall
        
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        try:
            if operation == "install" and package_id:
                command = f'winget install --id "{package_id}" --silent --accept-package-agreements --accept-source-agreements'
            elif operation == "uninstall" and package_id:
                command = f'winget uninstall --id "{package_id}" --silent'
            else:
                return False, "", f"Invalid winget operation: {operation}"
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes for installs
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Winget command timed out"
        except Exception as e:
            return False, "", str(e)
    
    @staticmethod
    def run_installer(installer_path: str, installer_type: str = None) -> Tuple[bool, str, str]:
        """
        Run an installer file with appropriate silent flags
        
        Args:
            installer_path: Path to the installer file
            installer_type: Type of installer ('exe', 'msi', 'msix'). Auto-detected if None
        
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        try:
            # Resolve the full path
            if not os.path.isabs(installer_path):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                installer_path = os.path.join(script_dir, installer_path)
            
            if not os.path.exists(installer_path):
                return False, "", f"Installer not found: {installer_path}"
            
            # Auto-detect installer type if not provided
            if not installer_type:
                ext = os.path.splitext(installer_path)[1].lower()
                if ext == '.msi':
                    installer_type = 'msi'
                elif ext == '.msix':
                    installer_type = 'msix'
                else:
                    installer_type = 'exe'
            
            # Build command with silent install flags - use proper escaping
            installer_path_escaped = installer_path.replace("'", "''").replace('$', '`$')
            
            if installer_type == 'msi':
                # MSI silent install using msiexec
                ps_command = f'$proc = Start-Process -FilePath "msiexec.exe" -ArgumentList "/i", \'{installer_path_escaped}\', "/quiet", "/norestart", "/qn" -Verb RunAs -PassThru; if ($proc) {{ $proc.WaitForExit(); exit $proc.ExitCode }} else {{ exit 1 }}'
            elif installer_type == 'msix':
                # MSIX install using Add-AppxPackage (requires admin)
                ps_command = f'$proc = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "Add-AppxPackage -Path \'{installer_path_escaped}\' -ErrorAction Stop" -Verb RunAs -PassThru; if ($proc) {{ $proc.WaitForExit(); exit $proc.ExitCode }} else {{ exit 1 }}'
            else:
                # EXE installer - try /S first (most common)
                ps_command = f'$proc = Start-Process -FilePath \'{installer_path_escaped}\' -ArgumentList "/S" -Verb RunAs -PassThru; if ($proc) {{ $proc.WaitForExit(); exit $proc.ExitCode }} else {{ exit 1 }}'
            
            result = subprocess.run(
                ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_command],
                shell=False,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Installer timed out after 600 seconds"
        except Exception as e:
            return False, "", str(e)
    
    @staticmethod
    def run_tool(tool_path: str, tool_type: str = None) -> Tuple[bool, str, str]:
        """
        Run a tool from the Tools folder with admin privileges
        
        Args:
            tool_path: Path to the tool file
            tool_type: Type of tool ('exe', 'ps1', 'bat', 'cmd'). Auto-detected if None
        
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        try:
            # Resolve the full path
            if not os.path.isabs(tool_path):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                tool_path = os.path.join(script_dir, tool_path)
            
            if not os.path.exists(tool_path):
                return False, "", f"Tool not found: {tool_path}"
            
            # Auto-detect tool type if not provided
            if not tool_type:
                ext = os.path.splitext(tool_path)[1].lower()
                tool_type = ext[1:] if ext.startswith('.') else ext
            
            # Run tool based on type - use proper PowerShell escaping
            # Escape single quotes and dollar signs for PowerShell
            tool_path_escaped = tool_path.replace("'", "''").replace('$', '`$')
            
            if tool_type == 'ps1':
                # PowerShell script - run with admin privileges
                ps_command = f'$proc = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", \'{tool_path_escaped}\' -Verb RunAs -PassThru; if ($proc) {{ $proc.WaitForExit(); exit $proc.ExitCode }} else {{ exit 1 }}'
            elif tool_type in ['bat', 'cmd']:
                # Batch file - run with admin privileges
                ps_command = f'$proc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", \'{tool_path_escaped}\' -Verb RunAs -PassThru; if ($proc) {{ $proc.WaitForExit(); exit $proc.ExitCode }} else {{ exit 1 }}'
            else:
                # EXE file - run with admin privileges
                ps_command = f'$proc = Start-Process -FilePath \'{tool_path_escaped}\' -Verb RunAs -PassThru; if ($proc) {{ $proc.WaitForExit(); exit $proc.ExitCode }} else {{ exit 1 }}'
            
            result = subprocess.run(
                ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_command],
                shell=False,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Tool timed out after 600 seconds"
        except Exception as e:
            return False, "", str(e)
    
    @staticmethod
    def run_executable(exe_path: str, args: List[str] = None, as_admin: bool = True) -> Tuple[bool, str, str]:
        """
        Execute an external executable file
        
        Args:
            exe_path: Path to the executable file
            args: List of arguments to pass to the executable
            as_admin: Whether to run as administrator (default: True)
        
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        try:
            # Resolve the full path
            if not os.path.isabs(exe_path):
                # If relative path, resolve relative to script directory
                script_dir = os.path.dirname(os.path.abspath(__file__))
                exe_path = os.path.join(script_dir, exe_path)
            
            # Check if file exists
            if not os.path.exists(exe_path):
                return False, "", f"Executable not found: {exe_path}"
            
            # Build command
            if args:
                cmd = [exe_path] + args
            else:
                cmd = exe_path
            
            if as_admin:
                # Run as administrator using PowerShell Start-Process
                # Escape path for PowerShell
                exe_path_escaped = exe_path.replace("'", "''").replace('$', '`$')
                
                if args:
                    # Convert args list to PowerShell array syntax with proper escaping
                    args_escaped = [arg.replace("'", "''").replace('$', '`$') for arg in args]
                    args_array = ','.join([f"'{arg}'" for arg in args_escaped])
                    ps_command = f'$proc = Start-Process -FilePath \'{exe_path_escaped}\' -ArgumentList {args_array} -Verb RunAs -PassThru; if ($proc) {{ $proc.WaitForExit(); exit $proc.ExitCode }} else {{ exit 1 }}'
                else:
                    ps_command = f'$proc = Start-Process -FilePath \'{exe_path_escaped}\' -Verb RunAs -PassThru; if ($proc) {{ $proc.WaitForExit(); exit $proc.ExitCode }} else {{ exit 1 }}'
                
                result = subprocess.run(
                    ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_command],
                    shell=False,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minutes timeout
                )
            else:
                # Run normally
                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Executable timed out after 600 seconds"
        except Exception as e:
            return False, "", str(e)
    
    @staticmethod
    def set_registry_value(key_path: str, value_name: str, value, hive: int = winreg.HKEY_LOCAL_MACHINE) -> Tuple[bool, str]:
        """
        Set a registry value (supports both integer and string values)
        
        Args:
            key_path: Registry key path (e.g., "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\DataCollection")
            value_name: Name of the value to set
            value: Value to set (int for REG_DWORD, str for REG_SZ)
            hive: Registry hive (HKEY_LOCAL_MACHINE or HKEY_CURRENT_USER)
        
        Returns:
            Tuple of (success: bool, error_message: str)
        """
        try:
            # Determine registry type based on value type
            if isinstance(value, int):
                reg_type = winreg.REG_DWORD
            elif isinstance(value, str):
                reg_type = winreg.REG_SZ
            else:
                return False, f"Unsupported value type: {type(value)}"
            
            # Open the registry key with write access
            key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, value_name, 0, reg_type, value)
            winreg.CloseKey(key)
            return True, ""
        except FileNotFoundError:
            # Key doesn't exist, create it
            try:
                # Determine registry type again for the new key
                if isinstance(value, int):
                    reg_type = winreg.REG_DWORD
                elif isinstance(value, str):
                    reg_type = winreg.REG_SZ
                else:
                    return False, f"Unsupported value type: {type(value)}"
                
                key = winreg.CreateKey(hive, key_path)
                winreg.SetValueEx(key, value_name, 0, reg_type, value)
                winreg.CloseKey(key)
                return True, ""
            except Exception as e:
                return False, str(e)
        except PermissionError:
            return False, "Administrator privileges required"
        except Exception as e:
            return False, str(e)


class WorkerThread(QThread):
    """Background thread for executing operations without freezing the UI"""
    
    log_signal = pyqtSignal(str, str)  # message, level
    progress_signal = pyqtSignal(int)  # percentage
    finished_signal = pyqtSignal(bool)  # success
    
    def __init__(self, operations: List[Dict], parent=None):
        super().__init__(parent)
        self.operations = operations
        self.cancelled = False
        self.success_count = 0
        self.failure_count = 0
    
    def run(self):
        """Execute all operations sequentially"""
        total_ops = len(self.operations)
        
        if total_ops == 0:
            self.log_signal.emit("No operations to execute", LogLevel.WARNING)
            self.finished_signal.emit(True)
            return
        
        self.log_signal.emit(f"Starting execution of {total_ops} operation(s)...", LogLevel.INFO)
        
        for idx, operation in enumerate(self.operations):
            if self.cancelled:
                self.log_signal.emit("Operation cancelled by user", LogLevel.WARNING)
                break
            
            op_type = operation.get('type')
            op_name = operation.get('name', 'Unknown operation')
            
            self.log_signal.emit(f"Executing: {op_name}", LogLevel.INFO)
            
            success = False
            error_msg = ""
            
            try:
                if op_type == 'winget_install':
                    package_id = operation.get('package_id')
                    if not package_id:
                        error_msg = "Package ID is missing"
                    else:
                        success, stdout, stderr = SystemOperations.run_winget(
                            'install',
                            package_id
                        )
                        if not success:
                            error_msg = stderr or stdout or "Winget installation failed"
                
                elif op_type == 'winget_uninstall':
                    package_id = operation.get('package_id')
                    if not package_id:
                        error_msg = "Package ID is missing"
                    else:
                        success, stdout, stderr = SystemOperations.run_winget(
                            'uninstall',
                            package_id
                        )
                        if not success:
                            error_msg = stderr or stdout or "Winget uninstallation failed"
                
                elif op_type == 'powershell':
                    command = operation.get('command')
                    if not command:
                        error_msg = "PowerShell command is missing"
                    else:
                        success, stdout, stderr = SystemOperations.run_powershell(command)
                        if not success:
                            error_msg = stderr or stdout or "PowerShell command failed"
                
                elif op_type == 'registry':
                    key_path = operation.get('key_path')
                    value_name = operation.get('value_name')
                    value = operation.get('value')
                    if not key_path or not value_name:
                        error_msg = "Registry key path or value name is missing"
                    else:
                        success, error_msg = SystemOperations.set_registry_value(
                            key_path,
                            value_name,
                            value,
                            operation.get('hive', winreg.HKEY_LOCAL_MACHINE)
                        )
                        if not success and not error_msg:
                            error_msg = "Registry operation failed"
                
                elif op_type == 'executable':
                    exe_path = operation.get('exe_path')
                    if not exe_path:
                        error_msg = "Executable path is missing"
                    else:
                        success, stdout, stderr = SystemOperations.run_executable(
                            exe_path,
                            operation.get('args', []),
                            operation.get('as_admin', True)
                        )
                        if not success:
                            error_msg = stderr or stdout or "Executable failed"
                
                elif op_type == 'local_installer':
                    installer_path = operation.get('path')
                    if not installer_path:
                        error_msg = "Installer path is missing"
                    else:
                        success, stdout, stderr = SystemOperations.run_installer(
                            installer_path,
                            operation.get('installer_type')
                        )
                        if not success:
                            error_msg = stderr or stdout or "Installer failed"
                
                elif op_type == 'tool':
                    tool_path = operation.get('path')
                    if not tool_path:
                        error_msg = "Tool path is missing"
                    else:
                        success, stdout, stderr = SystemOperations.run_tool(
                            tool_path,
                            operation.get('tool_type')
                        )
                        if not success:
                            # Combine stdout and stderr for better error reporting
                            error_details = ""
                            if stderr:
                                error_details += f"STDERR: {stderr[:500]}"
                            if stdout:
                                if error_details:
                                    error_details += " | "
                                error_details += f"STDOUT: {stdout[:500]}"
                            error_msg = error_details or "Tool failed (check logs for details)"
                else:
                    error_msg = f"Unknown operation type: {op_type}"
                
                if success:
                    self.success_count += 1
                    self.log_signal.emit(f"✓ {op_name} completed successfully", LogLevel.SUCCESS)
                else:
                    self.failure_count += 1
                    # Truncate long error messages
                    display_error = error_msg[:300] + "..." if len(error_msg) > 300 else error_msg
                    self.log_signal.emit(f"✗ {op_name} failed: {display_error}", LogLevel.ERROR)
            
            except Exception as e:
                self.failure_count += 1
                error_str = str(e)[:300] + "..." if len(str(e)) > 300 else str(e)
                self.log_signal.emit(f"✗ {op_name} error: {error_str}", LogLevel.ERROR)
            
            # Update progress
            progress = int((idx + 1) / total_ops * 100) if total_ops > 0 else 100
            self.progress_signal.emit(progress)
        
        # Execution summary
        self.log_signal.emit("", LogLevel.INFO)  # Empty line for readability
        self.log_signal.emit("=== Execution Summary ===", LogLevel.INFO)
        self.log_signal.emit(f"Total operations: {total_ops}", LogLevel.INFO)
        self.log_signal.emit(f"✓ Successful: {self.success_count}", LogLevel.SUCCESS)
        if self.failure_count > 0:
            self.log_signal.emit(f"✗ Failed: {self.failure_count}", LogLevel.ERROR)
        else:
            self.log_signal.emit("✗ Failed: 0", LogLevel.INFO)
        
        overall_success = self.failure_count == 0
        self.finished_signal.emit(overall_success)
    
    def cancel(self):
        """Cancel the operation"""
        self.cancelled = True


class ApplicationInstallerTab(QWidget):
    """Tab for installing applications via winget"""
    
    def __init__(self, log_callback, parent=None):
        super().__init__(parent)
        self.log_callback = log_callback
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI for application installer"""
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(6, 6, 6, 6)
        
        # Header
        header = QLabel("Application Installer")
        header.setToolTip("Install applications from the Apps folder")
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        info_label = QLabel(
            "Select applications to install. Applications from the Apps folder will be installed silently.\n"
            "Installations run sequentially to avoid conflicts."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #8b949e; font-size: 9pt; padding: 2px 0px;")
        layout.addWidget(info_label)
        
        # Scrollable area for checkboxes
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Scan Apps folder for installers
        script_dir = os.path.dirname(os.path.abspath(__file__))
        apps_folder = os.path.join(script_dir, "Apps")
        tools_folder = os.path.join(script_dir, "Tools")
        
        # Get list of files in Tools folder to exclude from Apps
        tools_files = set()
        if os.path.exists(tools_folder):
            tools_files = {f.lower() for f in os.listdir(tools_folder) if os.path.isfile(os.path.join(tools_folder, f))}
        
        self.apps = {}
        
        # Load apps from Apps folder (excluding those in Tools folder)
        if os.path.exists(apps_folder):
            for filename in os.listdir(apps_folder):
                # Skip if this file exists in Tools folder
                if filename.lower() in tools_files:
                    continue
                    
                file_path = os.path.join(apps_folder, filename)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ['.exe', '.msi', '.msix']:
                        # Clean up the name for display
                        app_name = os.path.splitext(filename)[0]
                        # Remove version numbers and common suffixes
                        app_name = app_name.replace('_windows_x64', '').replace('_x64', '').replace('_amd64', '')
                        app_name = app_name.replace('_setup', '').replace('_installer', '').replace('_portable', '')
                        app_name = app_name.replace('-', ' ').replace('_', ' ')
                        # Capitalize words
                        app_name = ' '.join(word.capitalize() for word in app_name.split())
                        
                        # Store relative path from script directory
                        relative_path = os.path.join("Apps", filename)
                        installer_type = ext[1:] if ext.startswith('.') else ext
                        
                        self.apps[app_name] = {
                            'type': 'local_installer',
                            'path': relative_path,
                            'installer_type': installer_type,
                            'filename': filename
                        }
        
        self.checkboxes = {}
        for app_name, app_info in self.apps.items():
            if isinstance(app_info, dict):
                # Local installer
                display_name = f"{app_name} (Local Installer)"
                checkbox = QCheckBox(display_name)
                checkbox.setChecked(False)
                self.checkboxes[app_name] = {
                    'checkbox': checkbox,
                    'type': app_info['type'],
                    'path': app_info['path'],
                    'installer_type': app_info['installer_type']
                }
            else:
                # Winget package (legacy support)
                checkbox = QCheckBox(app_name)
                checkbox.setChecked(False)
                self.checkboxes[app_name] = {'checkbox': checkbox, 'package_id': app_info, 'type': 'winget_install'}
            
            scroll_layout.addWidget(checkbox)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(4)
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all)
        self.select_all_btn.setStyleSheet("padding: 4px 10px; font-size: 9pt;")
        button_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        self.deselect_all_btn.setStyleSheet("padding: 4px 10px; font-size: 9pt;")
        button_layout.addWidget(self.deselect_all_btn)
        
        self.install_btn = QPushButton("Install Selected")
        self.install_btn.clicked.connect(self.install_selected)
        self.install_btn.setStyleSheet("background-color: #238636; color: white; font-weight: 600; border: none; padding: 4px 12px; font-size: 9pt;")
        button_layout.addWidget(self.install_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def select_all(self):
        """Select all application checkboxes"""
        for app_data in self.checkboxes.values():
            app_data['checkbox'].setChecked(True)
    
    def deselect_all(self):
        """Deselect all application checkboxes"""
        for app_data in self.checkboxes.values():
            app_data['checkbox'].setChecked(False)
    
    def install_selected(self):
        """Install all selected applications"""
        selected = []
        for app_name, app_data in self.checkboxes.items():
            if app_data['checkbox'].isChecked():
                if app_data.get('type') == 'local_installer':
                    # Local installer from Apps folder
                    selected.append({
                        'type': 'local_installer',
                        'name': f"Install {app_name}",
                        'path': app_data['path'],
                        'installer_type': app_data['installer_type']
                    })
                elif 'package_id' in app_data:
                    # Winget package
                    selected.append({
                        'type': 'winget_install',
                        'name': f"Install {app_name}",
                        'package_id': app_data['package_id']
                    })
        
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one application to install.")
            return
        
        return selected


class BloatwareRemovalTab(QWidget):
    """Tab for removing Windows bloatware"""
    
    def __init__(self, log_callback, parent=None):
        super().__init__(parent)
        self.log_callback = log_callback
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI for bloatware removal"""
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(6, 6, 6, 6)
        
        # Header
        header = QLabel("Bloatware Removal")
        header.setToolTip("Remove unwanted Windows apps and bloatware")
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        warning_label = QLabel(
            "⚠ WARNING: Removing Windows apps may affect system functionality.\n"
            "Only remove apps you are certain you don't need."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: #d29922; font-weight: 500; background-color: #1c2128; padding: 4px 8px; border-radius: 4px; border-left: 2px solid #d29922; font-size: 9pt;")
        layout.addWidget(warning_label)
        
        # Scrollable area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Bloatware apps to remove
        self.bloatware = {
            "Xbox Game Bar": {
                'command': 'Get-AppxPackage Microsoft.XboxGamingOverlay | Remove-AppxPackage',
                'description': 'Removes Xbox Game Bar overlay'
            },
            "Xbox Console Companion": {
                'command': 'Get-AppxPackage Microsoft.XboxApp | Remove-AppxPackage',
                'description': 'Removes Xbox Console Companion app'
            },
            "Xbox Identity Provider": {
                'command': 'Get-AppxPackage Microsoft.XboxIdentityProvider | Remove-AppxPackage',
                'description': 'Removes Xbox Identity Provider'
            },
            "OneDrive": {
                'command': '$onedriveProc = Get-Process -Name OneDrive -ErrorAction SilentlyContinue; if ($onedriveProc) { Stop-Process -Name OneDrive -Force -ErrorAction SilentlyContinue }; $setupPath = "$env:SystemRoot\\System32\\OneDriveSetup.exe"; if (Test-Path $setupPath) { Start-Process -FilePath $setupPath -ArgumentList "/uninstall" -Wait -NoNewWindow } else { Write-Error "OneDriveSetup.exe not found at $setupPath" }',
                'description': 'Uninstalls OneDrive (requires restart)'
            },
            "Cortana": {
                'command': 'Get-AppxPackage -allusers Microsoft.549981C3F5F10 | Remove-AppxPackage',
                'description': 'Removes Cortana voice assistant'
            },
            "Mixed Reality Portal": {
                'command': 'Get-AppxPackage Microsoft.MixedReality.Portal | Remove-AppxPackage',
                'description': 'Removes Windows Mixed Reality Portal'
            },
            "Feedback Hub": {
                'command': 'Get-AppxPackage Microsoft.WindowsFeedbackHub | Remove-AppxPackage',
                'description': 'Removes Feedback Hub app'
            },
            "Get Started": {
                'command': 'Get-AppxPackage Microsoft.Getstarted | Remove-AppxPackage',
                'description': 'Removes Get Started app'
            },
            "3D Viewer": {
                'command': 'Get-AppxPackage Microsoft.Microsoft3DViewer | Remove-AppxPackage',
            },
            "Paint 3D": {
                'command': 'Get-AppxPackage Microsoft.MSPaint | Remove-AppxPackage',
                'description': 'Removes Paint 3D app'
            },
            "Mail & Calendar": {
                'command': 'Get-AppxPackage microsoft.windowscommunicationsapps | Remove-AppxPackage',
                'description': 'Removes Mail and Calendar apps'
            },
            "Skype": {
                'command': 'Get-AppxPackage Microsoft.SkypeApp | Remove-AppxPackage',
                'description': 'Removes Skype app'
            },
            "Your Phone": {
                'command': 'Get-AppxPackage Microsoft.YourPhone | Remove-AppxPackage',
                'description': 'Removes Your Phone app'
            },
            "Sticky Notes": {
                'command': 'Get-AppxPackage Microsoft.MicrosoftStickyNotes | Remove-AppxPackage',
                'description': 'Removes Sticky Notes app'
            },
            "Weather": {
                'command': 'Get-AppxPackage Microsoft.BingWeather | Remove-AppxPackage',
                'description': 'Removes Weather app'
            },
            "News": {
                'command': 'Get-AppxPackage Microsoft.BingNews | Remove-AppxPackage',
                'description': 'Removes News app'
            },
            "Solitaire Collection": {
                'command': 'Get-AppxPackage Microsoft.MicrosoftSolitaireCollection | Remove-AppxPackage',
                'description': 'Removes Solitaire Collection'
            }
        }
        
        self.checkboxes = {}
        for app_name, app_info in self.bloatware.items():
            checkbox = QCheckBox(f"{app_name} - {app_info.get('description', 'Remove app')}")
            checkbox.setChecked(False)
            self.checkboxes[app_name] = {
                'checkbox': checkbox,
                'command': app_info['command']
            }
            scroll_layout.addWidget(checkbox)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(4)
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all)
        self.select_all_btn.setStyleSheet("padding: 4px 10px; font-size: 9pt;")
        button_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        self.deselect_all_btn.setStyleSheet("padding: 4px 10px; font-size: 9pt;")
        button_layout.addWidget(self.deselect_all_btn)
        
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected)
        self.remove_btn.setStyleSheet("background-color: #da3633; color: white; font-weight: 600; border: none; padding: 4px 12px; font-size: 9pt;")
        button_layout.addWidget(self.remove_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def select_all(self):
        """Select all bloatware checkboxes"""
        for app_data in self.checkboxes.values():
            app_data['checkbox'].setChecked(True)
    
    def deselect_all(self):
        """Deselect all bloatware checkboxes"""
        for app_data in self.checkboxes.values():
            app_data['checkbox'].setChecked(False)
    
    def remove_selected(self):
        """Get list of selected bloatware removal operations"""
        selected = []
        for app_name, app_data in self.checkboxes.items():
            if app_data['checkbox'].isChecked():
                selected.append({
                    'type': 'powershell',
                    'name': f"Remove {app_name}",
                    'command': app_data['command']
                })
        
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one app to remove.")
            return None
        
        return selected


class PrivacyTelemetryTab(QWidget):
    """Tab for disabling telemetry and privacy settings"""
    
    def __init__(self, log_callback, parent=None):
        super().__init__(parent)
        self.log_callback = log_callback
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI for privacy and telemetry settings"""
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(6, 6, 6, 6)
        
        # Header
        header = QLabel("Privacy & Telemetry")
        header.setToolTip("Disable Windows telemetry and data collection")
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        info_label = QLabel(
            "Disable Windows telemetry and data collection features.\n"
            "These changes modify registry settings and may require a restart."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #8b949e; font-size: 9pt; padding: 2px 0px;")
        layout.addWidget(info_label)
        
        # Scrollable area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Privacy and telemetry settings
        self.privacy_settings = {
            "Disable Telemetry": {
                'key_path': 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\DataCollection',
                'value_name': 'AllowTelemetry',
                'value': 0,
                'description': 'Disables Windows telemetry data collection',
                'hive': winreg.HKEY_LOCAL_MACHINE
            },
            "Disable Advertising ID": {
                'key_path': 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo',
                'value_name': 'Enabled',
                'value': 0,
                'description': 'Disables advertising ID tracking',
                'hive': winreg.HKEY_CURRENT_USER
            },
            "Disable Background App Access": {
                'key_path': 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications',
                'value_name': 'GlobalUserDisabled',
                'value': 1,
                'description': 'Disables background app access globally',
                'hive': winreg.HKEY_CURRENT_USER
            },
            "Disable Location Tracking": {
                'key_path': 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location',
                'value_name': 'Value',
                'value': 'Deny',
                'description': 'Disables location tracking',
                'hive': winreg.HKEY_CURRENT_USER
            },
            "Disable Diagnostic Data": {
                'key_path': 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\DataCollection',
                'value_name': 'AllowTelemetry',
                'value': 0,
                'description': 'Disables diagnostic data collection',
                'hive': winreg.HKEY_LOCAL_MACHINE
            },
            "Disable Tailored Experiences": {
                'key_path': 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Privacy',
                'value_name': 'TailoredExperiencesWithDiagnosticDataEnabled',
                'value': 0,
                'description': 'Disables tailored experiences based on diagnostic data',
                'hive': winreg.HKEY_CURRENT_USER
            },
            "Disable Activity History": {
                'key_path': 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Privacy',
                'value_name': 'EnableActivityFeed',
                'value': 0,
                'description': 'Disables activity history tracking',
                'hive': winreg.HKEY_CURRENT_USER
            },
            "Disable App Launch Tracking": {
                'key_path': 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced',
                'value_name': 'Start_TrackProgs',
                'value': 0,
                'description': 'Disables app launch tracking',
                'hive': winreg.HKEY_CURRENT_USER
            },
            "Disable Cortana Data Collection": {
                'key_path': 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Search',
                'value_name': 'CortanaConsent',
                'value': 0,
                'description': 'Disables Cortana data collection',
                'hive': winreg.HKEY_CURRENT_USER
            },
            "Disable Wi-Fi Sense": {
                'key_path': 'SOFTWARE\\Microsoft\\WcmSvc\\wifinetworkmanager\\config',
                'value_name': 'AutoConnectAllowedOEM',
                'value': 0,
                'description': 'Disables Wi-Fi Sense automatic connection',
                'hive': winreg.HKEY_LOCAL_MACHINE
            }
        }
        
        self.checkboxes = {}
        for setting_name, setting_info in self.privacy_settings.items():
            checkbox = QCheckBox(f"{setting_name} - {setting_info['description']}")
            checkbox.setChecked(False)
            self.checkboxes[setting_name] = {
                'checkbox': checkbox,
                'key_path': setting_info['key_path'],
                'value_name': setting_info['value_name'],
                'value': setting_info['value'],
                'hive': setting_info.get('hive', winreg.HKEY_LOCAL_MACHINE)
            }
            scroll_layout.addWidget(checkbox)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(4)
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all)
        self.select_all_btn.setStyleSheet("padding: 4px 10px; font-size: 9pt;")
        button_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        self.deselect_all_btn.setStyleSheet("padding: 4px 10px; font-size: 9pt;")
        button_layout.addWidget(self.deselect_all_btn)
        
        self.apply_btn = QPushButton("Apply Selected")
        self.apply_btn.clicked.connect(self.apply_selected)
        self.apply_btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: 600; border: none; padding: 4px 12px; font-size: 9pt;")
        button_layout.addWidget(self.apply_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def select_all(self):
        """Select all privacy settings"""
        for setting_data in self.checkboxes.values():
            setting_data['checkbox'].setChecked(True)
    
    def deselect_all(self):
        """Deselect all privacy settings"""
        for setting_data in self.checkboxes.values():
            setting_data['checkbox'].setChecked(False)
    
    def apply_selected(self):
        """Get list of selected privacy operations"""
        selected = []
        for setting_name, setting_data in self.checkboxes.items():
            if setting_data['checkbox'].isChecked():
                selected.append({
                    'type': 'registry',
                    'name': setting_name,
                    'key_path': setting_data['key_path'],
                    'value_name': setting_data['value_name'],
                    'value': setting_data['value'],
                    'hive': setting_data['hive']
                })
        
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one privacy setting to apply.")
            return None
        
        return selected


class ToolsTab(QWidget):
    """Tab for running tools from the Tools folder with admin privileges"""
    
    def __init__(self, log_callback, parent=None):
        super().__init__(parent)
        self.log_callback = log_callback
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI for tools"""
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(6, 6, 6, 6)
        
        # Header
        header = QLabel("Advanced Options")
        header.setToolTip("Run advanced tools from Tools folder with admin privileges")
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        info_label = QLabel(
            "Select tools to run. All tools will be executed with administrator privileges.\n"
            "Tools run sequentially to avoid conflicts."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #8b949e; font-size: 9pt; padding: 2px 0px;")
        layout.addWidget(info_label)
        
        # Scrollable area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Scan Tools folder
        script_dir = os.path.dirname(os.path.abspath(__file__))
        tools_folder = os.path.join(script_dir, "Tools")
        
        self.tools = {}
        
        # Load tools from Tools folder
        if os.path.exists(tools_folder):
            for filename in os.listdir(tools_folder):
                file_path = os.path.join(tools_folder, filename)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ['.exe', '.ps1', '.bat', '.cmd']:
                        # Clean up the name for display
                        tool_name = os.path.splitext(filename)[0]
                        tool_name = tool_name.replace('-', ' ').replace('_', ' ')
                        tool_name = ' '.join(word.capitalize() for word in tool_name.split())
                        
                        # Store relative path from script directory
                        relative_path = os.path.join("Tools", filename)
                        tool_type = ext[1:] if ext.startswith('.') else ext
                        
                        self.tools[tool_name] = {
                            'type': 'tool',
                            'path': relative_path,
                            'tool_type': tool_type,
                            'filename': filename
                        }
        
        self.checkboxes = {}
        for tool_name, tool_info in self.tools.items():
            checkbox = QCheckBox(f"{tool_name} ({tool_info['filename']})")
            checkbox.setChecked(False)
            self.checkboxes[tool_name] = {
                'checkbox': checkbox,
                'type': tool_info['type'],
                'path': tool_info['path'],
                'tool_type': tool_info['tool_type']
            }
            scroll_layout.addWidget(checkbox)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(4)
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all)
        self.select_all_btn.setStyleSheet("padding: 4px 10px; font-size: 9pt;")
        button_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        self.deselect_all_btn.setStyleSheet("padding: 4px 10px; font-size: 9pt;")
        button_layout.addWidget(self.deselect_all_btn)
        
        self.run_btn = QPushButton("Run Selected Tools")
        self.run_btn.clicked.connect(self.run_selected)
        self.run_btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: 600; border: none; padding: 4px 12px; font-size: 9pt;")
        button_layout.addWidget(self.run_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def select_all(self):
        """Select all tool checkboxes"""
        for tool_data in self.checkboxes.values():
            tool_data['checkbox'].setChecked(True)
    
    def deselect_all(self):
        """Deselect all tool checkboxes"""
        for tool_data in self.checkboxes.values():
            tool_data['checkbox'].setChecked(False)
    
    def run_selected(self):
        """Get list of selected tools to run"""
        selected = []
        for tool_name, tool_data in self.checkboxes.items():
            if tool_data['checkbox'].isChecked():
                selected.append({
                    'type': 'tool',
                    'name': f"Run {tool_name}",
                    'path': tool_data['path'],
                    'tool_type': tool_data['tool_type']
                })
        
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one tool to run.")
            return None
        
        return selected


class LogsTab(QWidget):
    """Tab for displaying real-time logs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI for logs"""
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(6, 6, 6, 6)
        
        # Header
        header = QLabel("Operation Logs")
        header.setToolTip("View real-time operation logs and status")
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 8))
        self.log_text.setStyleSheet("padding: 4px; line-height: 1.3;")
        
        # Dark theme for logs is handled by global stylesheet
        
        layout.addWidget(self.log_text)
        
        # Clear button
        clear_btn = QPushButton("Clear Logs")
        clear_btn.clicked.connect(self.clear_logs)
        clear_btn.setStyleSheet("padding: 4px 12px; font-size: 9pt;")
        layout.addWidget(clear_btn)
        
        self.setLayout(layout)
    
    def add_log(self, message: str, level: str = LogLevel.INFO):
        """Add a log entry"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Color coding based on level
        if level == LogLevel.SUCCESS:
            color = "#4CAF50"  # Green
        elif level == LogLevel.WARNING:
            color = "#FF9800"  # Orange
        elif level == LogLevel.ERROR:
            color = "#F44336"  # Red
        else:
            color = "#2196F3"  # Blue
        
        formatted_message = f'<span style="color: {color}">[{timestamp}] [{level}] {message}</span>'
        self.log_text.append(formatted_message)
        
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def clear_logs(self):
        """Clear all logs"""
        self.log_text.clear()


class Better10MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.worker_thread = None
        self.init_ui()
        self.check_admin_privileges()
    
    def init_ui(self):
        """Initialize the main UI"""
        self.setWindowTitle("Better10 - Windows 10 Post-Install Automation Tool")
        self.setGeometry(100, 100, 1100, 750)
        
        # Set minimum window size
        self.setMinimumSize(850, 550)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(8, 8, 8, 8)
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Tab widget with improved settings
        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(True)  # Enable scroll buttons if tabs don't fit
        self.tabs.setElideMode(Qt.ElideRight)  # Elide text if too long
        
        # Create tabs
        self.logs_tab = LogsTab()
        self.app_installer_tab = ApplicationInstallerTab(self.logs_tab.add_log)
        self.bloatware_tab = BloatwareRemovalTab(self.logs_tab.add_log)
        self.privacy_tab = PrivacyTelemetryTab(self.logs_tab.add_log)
        self.tools_tab = ToolsTab(self.logs_tab.add_log)
        
        # Add tabs with shorter names to prevent truncation
        self.tabs.addTab(self.app_installer_tab, "Apps")
        self.tabs.setTabToolTip(0, "Application Installer - Install applications from Apps folder")
        
        self.tabs.addTab(self.bloatware_tab, "Bloatware")
        self.tabs.setTabToolTip(1, "Bloatware Removal - Remove unwanted Windows apps")
        
        self.tabs.addTab(self.privacy_tab, "Privacy")
        self.tabs.setTabToolTip(2, "Privacy & Telemetry - Disable Windows telemetry and data collection")
        
        self.tabs.addTab(self.tools_tab, "Advanced")
        self.tabs.setTabToolTip(3, "Advanced Options - Run tools from Tools folder with admin privileges")
        
        self.tabs.addTab(self.logs_tab, "Logs")
        self.tabs.setTabToolTip(4, "Logs / Status - View operation logs and status")
        
        main_layout.addWidget(self.tabs)
        
        # Execute button with operation count
        execute_layout = QHBoxLayout()
        execute_layout.addStretch()
        
        self.operation_count_label = QLabel("0 operations selected")
        self.operation_count_label.setStyleSheet("color: #8b949e; font-size: 9pt; padding: 0px 8px;")
        execute_layout.addWidget(self.operation_count_label)
        
        self.execute_btn = QPushButton("Execute All Selected Operations")
        self.execute_btn.setStyleSheet(
            "background-color: #238636; color: white; font-weight: 600; font-size: 10pt; padding: 6px 16px; border: none; border-radius: 5px;"
        )
        self.execute_btn.clicked.connect(self.execute_all_operations)
        self.execute_btn.setToolTip("Execute all selected operations from all tabs (Ctrl+E)")
        execute_layout.addWidget(self.execute_btn)
        
        execute_layout.addStretch()
        main_layout.addLayout(execute_layout)
        
        # Update operation count when tabs change
        self.tabs.currentChanged.connect(self.update_operation_count)
        
        # Connect checkbox changes to update operation count
        self.connect_checkbox_signals()
        
        # Update operation count initially
        self.update_operation_count()
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
        # Initial log message
        self.logs_tab.add_log("Better10 initialized. Please select operations and click 'Execute All Selected Operations'.", LogLevel.INFO)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Ctrl+E to execute operations
        execute_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        execute_shortcut.activated.connect(self.execute_all_operations)
        
        # Ctrl+L to switch to logs tab
        logs_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        logs_shortcut.activated.connect(lambda: self.tabs.setCurrentIndex(4))
        
        # Ctrl+1-5 to switch tabs
        for i in range(5):
            tab_shortcut = QShortcut(QKeySequence(f"Ctrl+{i+1}"), self)
            tab_shortcut.activated.connect(lambda idx=i: self.tabs.setCurrentIndex(idx))
    
    def connect_checkbox_signals(self):
        """Connect all checkbox signals to update operation count"""
        # Application Installer tab
        for app_data in self.app_installer_tab.checkboxes.values():
            app_data['checkbox'].stateChanged.connect(self.update_operation_count)
        
        # Bloatware Removal tab
        for app_data in self.bloatware_tab.checkboxes.values():
            app_data['checkbox'].stateChanged.connect(self.update_operation_count)
        
        # Privacy & Telemetry tab
        for setting_data in self.privacy_tab.checkboxes.values():
            setting_data['checkbox'].stateChanged.connect(self.update_operation_count)
        
        # Advanced Options (Tools) tab
        for tool_data in self.tools_tab.checkboxes.values():
            tool_data['checkbox'].stateChanged.connect(self.update_operation_count)
    
    def update_operation_count(self):
        """Update the operation count label"""
        count = 0
        
        # Count from Application Installer
        for app_data in self.app_installer_tab.checkboxes.values():
            if app_data['checkbox'].isChecked():
                count += 1
        
        # Count from Bloatware Removal
        for app_data in self.bloatware_tab.checkboxes.values():
            if app_data['checkbox'].isChecked():
                count += 1
        
        # Count from Privacy & Telemetry
        for setting_data in self.privacy_tab.checkboxes.values():
            if setting_data['checkbox'].isChecked():
                count += 1
        
        # Count from Advanced Options (Tools)
        for tool_data in self.tools_tab.checkboxes.values():
            if tool_data['checkbox'].isChecked():
                count += 1
        
        # Update label
        if count == 0:
            self.operation_count_label.setText("0 operations selected")
            self.operation_count_label.setStyleSheet("color: #8b949e; font-size: 9pt; padding: 0px 10px;")
        else:
            self.operation_count_label.setText(f"{count} operation(s) selected")
            self.operation_count_label.setStyleSheet("color: #58a6ff; font-size: 9pt; padding: 0px 10px; font-weight: 500;")
    
    def check_admin_privileges(self):
        """Check if running with administrator privileges"""
        if not SystemOperations.is_admin():
            self.logs_tab.add_log(
                "WARNING: Application is not running with administrator privileges.",
                LogLevel.WARNING
            )
            self.logs_tab.add_log(
                "Many operations require admin rights. Please restart as administrator.",
                LogLevel.WARNING
            )
            
            reply = QMessageBox.warning(
                self,
                "Administrator Privileges Required",
                "This application requires administrator privileges to function properly.\n\n"
                "Please restart the application as administrator.",
                QMessageBox.Ok
            )
        else:
            self.logs_tab.add_log("Running with administrator privileges.", LogLevel.SUCCESS)
    
    def execute_all_operations(self):
        """Collect all selected operations from all tabs and execute them"""
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Operation in Progress", "An operation is already in progress. Please wait.")
            return
        
        # Collect operations from all tabs
        all_operations = []
        
        # Application installer
        selected_apps = []
        for app_name, app_data in self.app_installer_tab.checkboxes.items():
            if app_data['checkbox'].isChecked():
                if app_data.get('type') == 'local_installer':
                    # Local installer from Apps folder
                    selected_apps.append({
                        'type': 'local_installer',
                        'name': f"Install {app_name}",
                        'path': app_data['path'],
                        'installer_type': app_data['installer_type']
                    })
                elif 'package_id' in app_data:
                    # Winget package
                    selected_apps.append({
                        'type': 'winget_install',
                        'name': f"Install {app_name}",
                        'package_id': app_data['package_id']
                    })
        all_operations.extend(selected_apps)
        
        # Bloatware removal
        for app_name, app_data in self.bloatware_tab.checkboxes.items():
            if app_data['checkbox'].isChecked():
                all_operations.append({
                    'type': 'powershell',
                    'name': f"Remove {app_name}",
                    'command': app_data['command']
                })
        
        # Privacy settings
        for setting_name, setting_data in self.privacy_tab.checkboxes.items():
            if setting_data['checkbox'].isChecked():
                all_operations.append({
                    'type': 'registry',
                    'name': setting_name,
                    'key_path': setting_data['key_path'],
                    'value_name': setting_data['value_name'],
                    'value': setting_data['value'],
                    'hive': setting_data['hive']
                })
        
        # Tools from Tools folder (Advanced Options)
        for tool_name, tool_data in self.tools_tab.checkboxes.items():
            if tool_data['checkbox'].isChecked():
                all_operations.append({
                    'type': 'tool',
                    'name': f"Run {tool_name}",
                    'path': tool_data['path'],
                    'tool_type': tool_data['tool_type']
                })
        
        if not all_operations:
            QMessageBox.information(self, "No Operations Selected", "Please select at least one operation to execute.")
            return
        
        # Check for Windows Defender operations
        defender_ops = [op for op in all_operations if "Defender" in op.get('name', '') or "defender" in op.get('name', '').lower()]
        
        # Special confirmation for Windows Defender operations
        if defender_ops:
            defender_msg = "\n".join([f"  • {op['name']}" for op in defender_ops])
            reply = QMessageBox.warning(
                self,
                "⚠️ CRITICAL WARNING - Windows Defender Removal",
                f"<b><font size='+1' color='#ff5252'>YOU ARE ABOUT TO REMOVE/DISABLE WINDOWS DEFENDER!</font></b><br><br>"
                f"<b>Selected Defender operations:</b><br>{defender_msg}<br><br>"
                f"<b>⚠️ THIS WILL SIGNIFICANTLY REDUCE YOUR SYSTEM SECURITY!</b><br><br>"
                f"• Windows Defender is your primary antivirus protection<br>"
                f"• Removing it leaves your system vulnerable to malware<br>"
                f"• This action is <b>DIFFICULT TO REVERSE</b><br>"
                f"• Only proceed if you have alternative antivirus installed<br><br>"
                f"<b>Are you absolutely certain you want to proceed?</b>",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            # Second confirmation for Defender operations
            reply2 = QMessageBox.warning(
                self,
                "⚠️ FINAL CONFIRMATION REQUIRED",
                f"<b><font size='+1' color='#ff5252'>LAST CHANCE TO CANCEL</font></b><br><br>"
                f"You are about to remove/disable Windows Defender.<br><br>"
                f"<b>This action cannot be easily undone.</b><br><br>"
                f"Are you <b>100% SURE</b> you want to continue?<br><br>"
                f"Click <b>NO</b> to cancel safely.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply2 == QMessageBox.No:
                return
        
        # General confirmation dialog with operation summary
        operations_summary = []
        operation_types = {}
        for op in all_operations:
            op_type = op.get('type', 'unknown')
            operation_types[op_type] = operation_types.get(op_type, 0) + 1
        
        summary_lines = [f"Total: {len(all_operations)} operation(s)"]
        if operation_types.get('winget_install') or operation_types.get('local_installer'):
            install_count = operation_types.get('winget_install', 0) + operation_types.get('local_installer', 0)
            summary_lines.append(f"  • {install_count} application(s) to install")
        if operation_types.get('powershell'):
            summary_lines.append(f"  • {operation_types['powershell']} bloatware removal(s)")
        if operation_types.get('registry'):
            summary_lines.append(f"  • {operation_types['registry']} privacy setting(s)")
        if operation_types.get('tool'):
            summary_lines.append(f"  • {operation_types['tool']} tool(s) to run")
        
        summary_text = "\n".join(summary_lines)
        
        reply = QMessageBox.question(
            self,
            "Confirm Execution",
            f"<b>You are about to execute:</b><br><br>{summary_text.replace(chr(10), '<br>')}<br><br>"
            "<b>This will make system-level changes.</b><br><br>"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # Execute operations
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)
        self.execute_btn.setEnabled(False)
        self.statusBar().showMessage(f"Executing {len(all_operations)} operation(s)...")
        
        self.worker_thread = WorkerThread(all_operations)
        self.worker_thread.log_signal.connect(self.logs_tab.add_log)
        self.worker_thread.progress_signal.connect(self.progress_bar.setValue)
        self.worker_thread.finished_signal.connect(self.on_operations_finished)
        self.worker_thread.start()
    
    def on_operations_finished(self, success: bool):
        """Called when all operations are finished"""
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.execute_btn.setEnabled(True)
        self.logs_tab.add_log("All operations completed.", LogLevel.INFO)
        self.statusBar().showMessage("Ready - Operations completed")
        self.update_operation_count()  # Update count after operations


def is_admin():
    """Check if running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def run_as_admin():
    """Re-launch the application with administrator privileges"""
    if is_admin():
        return True
    
    # Re-run the program with admin rights
    try:
        if getattr(sys, 'frozen', False):
            # If running as compiled executable (PyInstaller, etc.)
            script_path = sys.executable
            params = ""
        else:
            # If running as Python script
            script_path = sys.executable  # Python interpreter
            script_file = __file__
            # Build parameters: script file + any original arguments
            params_list = [f'"{script_file}"']
            if len(sys.argv) > 1:
                params_list.extend([f'"{arg}"' for arg in sys.argv[1:]])
            params = ' '.join(params_list)
        
        # Use ShellExecute to run as admin
        # ShellExecuteW signature: (hwnd, operation, file, parameters, directory, showCmd)
        result = ctypes.windll.shell32.ShellExecuteW(
            None,  # No parent window
            "runas",  # Operation: run as administrator (triggers UAC)
            script_path,  # Application to run (Python interpreter or exe)
            params,  # Parameters (script file + args)
            None,  # Working directory (None = current)
            1  # Show window normally (SW_SHOWNORMAL)
        )
        
        # ShellExecute returns a value > 32 if successful
        # Values <= 32 indicate errors
        if result > 32:
            return False  # Successfully launched elevated version, exit this instance
        else:
            # Error codes
            error_messages = {
                0: "Out of memory or resources",
                2: "File not found",
                3: "Path not found",
                5: "Access denied",
                8: "Out of memory",
                11: "Invalid .exe file",
                26: "Sharing violation",
                27: "File association incomplete or invalid",
                28: "DDE transaction timed out",
                29: "DDE transaction failed",
                30: "DDE transaction busy",
                31: "No file association",
                32: "DLL not found"
            }
            error_msg = error_messages.get(result, f"Unknown error (code: {result})")
            print(f"Failed to elevate privileges: {error_msg}")
            return True  # Failed to elevate, continue anyway
    except Exception as e:
        print(f"Failed to elevate privileges: {e}")
        return True  # Failed to elevate, continue anyway


def main():
    """Main entry point"""
    # Check if running as admin, if not, elevate and restart
    if not is_admin():
        print("="*60)
        print("Better10 requires administrator privileges")
        print("="*60)
        print("Requesting elevation... A UAC prompt will appear.")
        print("Please click 'Yes' to continue.\n")
        
        # Try to elevate
        elevation_success = run_as_admin()
        
        # If elevation was attempted (launched new process), exit this instance
        # run_as_admin() returns False if it successfully launched the elevated instance
        if not elevation_success:
            # Successfully launched elevated version, exit this instance
            print("Elevated instance launched. This window will close...")
            import time
            time.sleep(2)  # Give user time to see the message
            sys.exit(0)
        
        # If we get here, elevation failed (user cancelled UAC or error occurred)
        print("\n" + "="*60)
        print("Elevation cancelled or failed.")
        print("="*60)
        print("This application requires administrator privileges to function properly.")
        print("\nTo run as administrator:")
        print("1. Right-click 'better10.py'")
        print("2. Select 'Run as administrator'")
        print("="*60 + "\n")
        
        # Still launch the GUI but show warning
        # User can choose to continue or close
    
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Apply modern compact dark theme stylesheet
    dark_stylesheet = """
    QMainWindow {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    QWidget {
        background-color: #0d1117;
        color: #c9d1d9;
        font-size: 9pt;
    }
    QTabWidget::pane {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        top: -1px;
    }
    QTabBar {
        background-color: #161b22;
    }
    QTabBar::tab {
        background-color: #161b22;
        color: #8b949e;
        padding: 6px 14px;
        margin-right: 1px;
        border: none;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        font-size: 9pt;
        font-weight: 500;
        min-width: 70px;
        max-width: 180px;
    }
    QTabBar::tab:selected {
        background-color: #0d1117;
        color: #58a6ff;
        border-bottom: 2px solid #58a6ff;
        font-weight: 600;
    }
    QTabBar::tab:hover:!selected {
        background-color: #21262d;
        color: #c9d1d9;
    }
    QTabBar::scroller {
        width: 30px;
    }
    QTabBar QToolButton {
        background-color: #21262d;
        color: #8b949e;
        border: none;
        border-radius: 4px;
    }
    QTabBar QToolButton:hover {
        background-color: #30363d;
        color: #c9d1d9;
    }
    QPushButton {
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        padding: 4px 12px;
        border-radius: 5px;
        font-size: 9pt;
        font-weight: 500;
        min-height: 24px;
    }
    QPushButton:hover {
        background-color: #30363d;
        border-color: #484f58;
    }
    QPushButton:pressed {
        background-color: #161b22;
    }
    QCheckBox {
        color: #c9d1d9;
        spacing: 5px;
        font-size: 9pt;
        padding: 1px;
    }
    QCheckBox::indicator {
        width: 15px;
        height: 15px;
        border: 1.5px solid #30363d;
        background-color: #161b22;
        border-radius: 3px;
    }
    QCheckBox::indicator:hover {
        border-color: #58a6ff;
        background-color: #21262d;
    }
    QCheckBox::indicator:checked {
        background-color: #238636;
        border-color: #238636;
    }
    QLabel {
        color: #c9d1d9;
        font-size: 9pt;
    }
    QTextEdit {
        background-color: #0d1117;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 5px;
        padding: 6px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 8.5pt;
    }
    QScrollArea {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 5px;
    }
    QScrollBar:vertical {
        background-color: #161b22;
        width: 10px;
        border: none;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background-color: #30363d;
        min-height: 20px;
        border-radius: 5px;
        margin: 2px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #484f58;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QProgressBar {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 5px;
        text-align: center;
        color: #c9d1d9;
        height: 18px;
        font-size: 8.5pt;
    }
    QProgressBar::chunk {
        background-color: #238636;
        border-radius: 4px;
    }
    QStatusBar {
        background-color: #161b22;
        color: #8b949e;
        border-top: 1px solid #30363d;
        font-size: 9pt;
    }
    QMessageBox {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    QMessageBox QLabel {
        color: #c9d1d9;
    }
    QMessageBox QPushButton {
        background-color: #21262d;
        color: #c9d1d9;
        min-width: 80px;
        padding: 6px 14px;
        border: 1px solid #30363d;
    }
    QMessageBox QPushButton:hover {
        background-color: #30363d;
    }
    """
    app.setStyleSheet(dark_stylesheet)
    
    window = Better10MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

