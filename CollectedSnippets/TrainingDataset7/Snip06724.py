def _get_spatialite_func(self, func):
        """
        Helper routine for calling SpatiaLite functions and returning
        their result.
        Any error occurring in this method should be handled by the caller.
        """
        cursor = self.connection._cursor()
        try:
            cursor.execute("SELECT %s" % func)
            row = cursor.fetchone()
        finally:
            cursor.close()
        return row[0]