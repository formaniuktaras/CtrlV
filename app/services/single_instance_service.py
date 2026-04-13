from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

LOGGER = logging.getLogger(__name__)


class SingleInstanceService(QObject):
    """Qt local-socket based single-instance coordinator."""

    activation_requested = Signal()

    def __init__(self, server_name: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._server_name = server_name
        self._server: QLocalServer | None = None

    def try_acquire_primary(self) -> bool:
        if self._try_notify_primary():
            LOGGER.info("Secondary instance detected; notified primary instance")
            return False

        QLocalServer.removeServer(self._server_name)
        server = QLocalServer(self)
        if not server.listen(self._server_name):
            LOGGER.warning("Unable to listen single-instance socket: %s", server.errorString())
            return True

        server.newConnection.connect(self._on_new_connection)
        self._server = server
        LOGGER.info("Primary single-instance server acquired: %s", self._server_name)
        return True

    def shutdown(self) -> None:
        if self._server is None:
            return
        self._server.close()
        QLocalServer.removeServer(self._server_name)
        self._server = None

    def _try_notify_primary(self) -> bool:
        socket = QLocalSocket(self)
        socket.connectToServer(self._server_name)
        if not socket.waitForConnected(150):
            socket.abort()
            return False

        socket.write(b"show")
        socket.flush()
        socket.waitForBytesWritten(150)
        socket.disconnectFromServer()
        return True

    def _on_new_connection(self) -> None:
        if self._server is None:
            return

        socket = self._server.nextPendingConnection()
        if socket is None:
            return

        socket.waitForReadyRead(150)
        message = bytes(socket.readAll()).decode(errors="ignore").strip().lower()
        socket.disconnectFromServer()
        socket.deleteLater()

        if message == "show":
            LOGGER.info("Primary instance activation request received")
            self.activation_requested.emit()
