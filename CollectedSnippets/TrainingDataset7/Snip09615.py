def init_connection_state(self):
        super().init_connection_state()
        cursor = self.create_cursor()
        # Set the territory first. The territory overrides NLS_DATE_FORMAT
        # and NLS_TIMESTAMP_FORMAT to the territory default. When all of
        # these are set in single statement it isn't clear what is supposed
        # to happen.
        cursor.execute("ALTER SESSION SET NLS_TERRITORY = 'AMERICA'")
        # Set Oracle date to ANSI date format. This only needs to execute
        # once when we create a new connection. We also set the Territory
        # to 'AMERICA' which forces Sunday to evaluate to a '1' in
        # TO_CHAR().
        cursor.execute(
            "ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'"
            " NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF'"
            + (" TIME_ZONE = 'UTC'" if settings.USE_TZ else "")
        )
        cursor.close()
        if "operators" not in self.__dict__:
            # Ticket #14149: Check whether our LIKE implementation will
            # work for this connection or we need to fall back on LIKEC.
            # This check is performed only once per DatabaseWrapper
            # instance per thread, since subsequent connections will use
            # the same settings.
            cursor = self.create_cursor()
            try:
                cursor.execute(
                    "SELECT 1 FROM DUAL WHERE DUMMY %s"
                    % self._standard_operators["contains"],
                    ["X"],
                )
            except Database.DatabaseError:
                self.operators = self._likec_operators
                self.pattern_ops = self._likec_pattern_ops
            else:
                self.operators = self._standard_operators
                self.pattern_ops = self._standard_pattern_ops
            cursor.close()
        self.connection.stmtcachesize = 20
        # Ensure all changes are preserved even when AUTOCOMMIT is False.
        if not self.get_autocommit():
            self.commit()