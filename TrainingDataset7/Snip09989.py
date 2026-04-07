def get_primary_key_columns(self, cursor, table_name):
        cursor.execute(
            "PRAGMA table_info(%s)" % self.connection.ops.quote_name(table_name)
        )
        return [name for _, name, *_, pk in cursor.fetchall() if pk]