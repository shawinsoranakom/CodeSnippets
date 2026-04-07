def _execute_raise_database_already_exists(self, cursor, parameters, keepdb=False):
        error = errors.DuplicateDatabase(
            "database %s already exists" % parameters["dbname"]
        )
        raise DatabaseError() from error