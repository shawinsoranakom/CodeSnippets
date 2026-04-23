def savepoint(self):
        """
        Create a savepoint inside the current transaction. Return an
        identifier for the savepoint that will be used for the subsequent
        rollback or commit. Do nothing if savepoints are not supported.
        """
        if not self._savepoint_allowed():
            return

        thread_ident = _thread.get_ident()
        tid = str(thread_ident).replace("-", "")

        self.savepoint_state += 1
        sid = "s%s_x%d" % (tid, self.savepoint_state)

        self.validate_thread_sharing()
        self._savepoint(sid)

        return sid