from __future__ import annotations

import sys

from app.bootstrap import create_application


def main() -> int:
    app = create_application(sys.argv)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
