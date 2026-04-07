def _execute_raise_database_exists(self, cursor, parameters, keepdb=False):
        raise DatabaseError(
            1007, "Can't create database '%s'; database exists" % parameters["dbname"]
        )