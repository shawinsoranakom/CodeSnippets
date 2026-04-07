def alter_db_table_comment(self, model, old_db_table_comment, new_db_table_comment):
        if self.sql_alter_table_comment and self.connection.features.supports_comments:
            self.execute(
                self.sql_alter_table_comment
                % {
                    "table": self.quote_name(model._meta.db_table),
                    "comment": self.quote_value(new_db_table_comment or ""),
                }
            )