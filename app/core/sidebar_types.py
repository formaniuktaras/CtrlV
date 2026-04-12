from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DockSide(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class PanelState(str, Enum):
    EXPANDED = "expanded"
    COLLAPSED = "collapsed"


class RuntimeState(str, Enum):
    FLOATING = "floating"
    DOCKED_EXPANDED = "docked_expanded"
    DOCKED_COLLAPSED = "docked_collapsed"
    DRAGGING = "dragging"
    ANIMATING_EXPAND = "animating_expand"
    ANIMATING_COLLAPSE = "animating_collapse"


@dataclass(slots=True)
class SidebarSettings:
    width: int = 420
    height: int = 640
    expanded_x: int = 0
    expanded_y: int = 120
    dock_side: DockSide = DockSide.RIGHT
    panel_state: PanelState = PanelState.EXPANDED
    visible_edge_px: int = 8
    auto_hide_enabled: bool = True
    always_on_top: bool = True
    reveal_trigger_px: int = 3
    reveal_vertical_tolerance_px: int = 80


@dataclass(slots=True)
class TraySettings:
    close_to_tray_enabled: bool = True
    tray_click_action: str = "toggle_sidebar"
    always_on_top: bool = True
    auto_hide_enabled: bool = True
