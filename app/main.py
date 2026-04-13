from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from app.bootstrap import create_application

LOGGER = logging.getLogger(__name__)


def main() -> int:
    try:
        app = create_application(sys.argv)
        return app.exec()
    except Exception:
        LOGGER.exception("Fatal startup failure")
        fallback_app = QApplication.instance() or QApplication([])
        QMessageBox.critical(
            None,
            "CtrlV startup error",
            "CtrlV failed to start. Open the logs folder for details.",
        )
        if fallback_app is not None:
            fallback_app.quit()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
