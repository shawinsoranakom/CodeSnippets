def _savepoint(self, sid):
        with self.cursor() as cursor:
            cursor.execute(self.ops.savepoint_create_sql(sid))