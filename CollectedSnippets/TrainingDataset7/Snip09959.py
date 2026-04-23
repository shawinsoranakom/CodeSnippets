def disable_constraint_checking(self):
        with self.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = OFF")
            # Foreign key constraints cannot be turned off while in a multi-
            # statement transaction. Fetch the current state of the pragma
            # to determine if constraints are effectively disabled.
            enabled = cursor.execute("PRAGMA foreign_keys").fetchone()[0]
        return not bool(enabled)