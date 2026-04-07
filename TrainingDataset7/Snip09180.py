def _savepoint_commit(self, sid):
        with self.cursor() as cursor:
            cursor.execute(self.ops.savepoint_commit_sql(sid))