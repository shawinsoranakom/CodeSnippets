def bulk_insert_sql(self, fields, placeholder_rows):
        if isinstance(placeholder_rows, InsertUnnest):
            return f"SELECT * FROM {placeholder_rows}"
        return super().bulk_insert_sql(fields, placeholder_rows)