def _is_identity_column(self, table_name, column_name):
        if not column_name:
            return False
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    CASE WHEN identity_column = 'YES' THEN 1 ELSE 0 END
                FROM user_tab_cols
                WHERE table_name = %s AND
                      column_name = %s
                """,
                [self.normalize_name(table_name), self.normalize_name(column_name)],
            )
            row = cursor.fetchone()
            return row[0] if row else False