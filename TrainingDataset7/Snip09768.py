def _drop_identity(self, table_name, column_name):
        self.execute(
            "ALTER TABLE %(table)s MODIFY %(column)s DROP IDENTITY"
            % {
                "table": self.quote_name(table_name),
                "column": self.quote_name(column_name),
            }
        )