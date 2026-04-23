def _get_postgis_func(self, func):
        """
        Helper routine for calling PostGIS functions and returning their
        result.
        """
        # Close out the connection. See #9437.
        with self.connection.temporary_connection() as cursor:
            cursor.execute("SELECT %s()" % func)
            return cursor.fetchone()[0]