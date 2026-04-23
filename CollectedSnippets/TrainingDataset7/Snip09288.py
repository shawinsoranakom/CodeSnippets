def bulk_insert_sql(self, fields, placeholder_rows):
        placeholder_rows_sql = (", ".join(row) for row in placeholder_rows)
        values_sql = ", ".join([f"({sql})" for sql in placeholder_rows_sql])
        return f"VALUES {values_sql}"