def _savepoint_commit(self, sid):
        if self.queries_logged:
            self.queries_log.append(
                {
                    "sql": "-- RELEASE SAVEPOINT %s (faked)" % self.ops.quote_name(sid),
                    "time": "0.000",
                }
            )