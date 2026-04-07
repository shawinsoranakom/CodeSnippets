def savepoint_commit(self, sid):
        """
        Release a savepoint. Do nothing if savepoints are not supported.
        """
        if not self._savepoint_allowed():
            return

        self.validate_thread_sharing()
        self._savepoint_commit(sid)