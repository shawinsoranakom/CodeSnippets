def copy_to(self, file, table, *args, **kwargs):
            with self.debug_sql(sql="COPY %s TO STDOUT" % table):
                return self.cursor.copy_to(file, table, *args, **kwargs)