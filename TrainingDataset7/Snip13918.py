def _should_reload_connections(self):
        if self._databases_support_transactions():
            return False
        return super()._should_reload_connections()