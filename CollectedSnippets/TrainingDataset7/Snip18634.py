def _execute_raise_permission_denied(self, cursor, parameters, keepdb=False):
        error = errors.InsufficientPrivilege("permission denied to create database")
        raise DatabaseError() from error