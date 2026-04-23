def get_sequences(self, cursor, table_name, table_fields=()):
        pk_col = self.get_primary_key_column(cursor, table_name)
        return [{"table": table_name, "column": pk_col}]