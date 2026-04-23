def _delete_index_sql(self, model, name, sql=None):
        statement = Statement(
            sql or self.sql_delete_index,
            table=Table(model._meta.db_table, self.quote_name),
            name=self.quote_name(name),
        )

        # Remove all deferred statements referencing the deleted index.
        table_name = statement.parts["table"].table
        index_name = statement.parts["name"]
        for sql in list(self.deferred_sql):
            if isinstance(sql, Statement) and sql.references_index(
                table_name, index_name
            ):
                self.deferred_sql.remove(sql)

        return statement