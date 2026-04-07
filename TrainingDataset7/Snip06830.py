def get_db_prep_lookup(self, value, connection):
        # get_db_prep_lookup is called by process_rhs from super class
        return ("%s", (connection.ops.Adapter(value),))