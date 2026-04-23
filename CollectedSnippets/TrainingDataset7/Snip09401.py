def _rename_index_sql(self, model, old_name, new_name):
        return Statement(
            self.sql_rename_index,
            table=Table(model._meta.db_table, self.quote_name),
            old_name=self.quote_name(old_name),
            new_name=self.quote_name(new_name),
        )