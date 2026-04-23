def _delete_index_sql(self, model, name, sql=None, concurrently=False):
        sql = sql or (
            self.sql_delete_index_concurrently
            if concurrently
            else self.sql_delete_index
        )
        return super()._delete_index_sql(model, name, sql)