def enable_constraint_checking(self):
        with self.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = ON")