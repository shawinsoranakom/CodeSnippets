def copy(self, statement):
            with self.debug_sql(statement):
                return self.cursor.copy(statement)