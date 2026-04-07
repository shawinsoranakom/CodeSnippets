def _savepoint_rollback(self, sid):
        with self.cursor() as cursor:
            cursor.execute(self.ops.savepoint_rollback_sql(sid))