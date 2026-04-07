def allows_auto_pk_0(self):
        """
        Autoincrement primary key can be set to 0 if it doesn't generate new
        autoincrement values.
        """
        return "NO_AUTO_VALUE_ON_ZERO" in self.connection.sql_mode