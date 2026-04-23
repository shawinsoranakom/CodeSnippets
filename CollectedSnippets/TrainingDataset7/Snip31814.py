def _close_connections(self):
        super()._close_connections()
        self._connections_closed.set()