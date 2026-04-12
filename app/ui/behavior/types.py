from __future__ import annotations

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
