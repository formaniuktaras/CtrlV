"""Application service layer."""

from app.services.app_lifecycle import AppLifecycleController
from app.services.autostart_service import AutostartError, AutostartService
from app.services.settings_service import SettingsService, SidebarSettings, TraySettings
from app.services.single_instance_service import SingleInstanceService
from app.services.tray_service import TrayMenuState, TrayService

__all__ = [
    "AppLifecycleController",
    "AutostartError",
    "AutostartService",
    "SettingsService",
    "SingleInstanceService",
    "SidebarSettings",
    "TraySettings",
    "TrayMenuState",
    "TrayService",
]
