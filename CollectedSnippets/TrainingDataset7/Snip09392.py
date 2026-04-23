def _alter_column_comment_sql(self, model, new_field, new_type, new_db_comment):
        return (
            self.sql_alter_column_comment
            % {
                "table": self.quote_name(model._meta.db_table),
                "column": self.quote_name(new_field.column),
                "comment": self._comment_sql(new_db_comment),
            },
            [],
        )