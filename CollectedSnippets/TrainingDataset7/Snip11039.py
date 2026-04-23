def db_check(self, connection):
        """
        Return the database column check constraint for this field, for the
        provided connection. Works the same way as db_type() for the case that
        get_internal_type() does not map to a preexisting model field.
        """
        data = self.db_type_parameters(connection)
        try:
            return (
                connection.data_type_check_constraints[self.get_internal_type()] % data
            )
        except KeyError:
            return None