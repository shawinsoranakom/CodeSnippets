def _nodb_cursor(self):
        """
        Return a cursor from an alternative connection to be used when there is
        no need to access the main database, specifically for test db
        creation/deletion. This also prevents the production database from
        being exposed to potential child threads while (or after) the test
        database is destroyed. Refs #10868, #17786, #16969.
        """
        conn = self.__class__({**self.settings_dict, "NAME": None}, alias=NO_DB_ALIAS)
        try:
            with conn.cursor() as cursor:
                yield cursor
        finally:
            conn.close()