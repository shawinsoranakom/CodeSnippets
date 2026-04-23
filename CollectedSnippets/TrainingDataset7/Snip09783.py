def get_database_version(self):
        """
        Return a tuple of the database's version.
        E.g. for pg_version 120004, return (12, 4).
        """
        return divmod(self.pg_version, 10000)