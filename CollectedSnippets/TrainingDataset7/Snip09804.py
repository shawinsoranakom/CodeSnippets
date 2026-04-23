def copy_expert(self, sql, file, *args):
            with self.debug_sql(sql):
                return self.cursor.copy_expert(sql, file, *args)