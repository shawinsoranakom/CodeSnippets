def _execute_raise_access_denied(self, cursor, parameters, keepdb=False):
        raise DatabaseError(1044, "Access denied for user")