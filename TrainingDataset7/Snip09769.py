def _get_default_collation(self, table_name):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT default_collation FROM user_tables WHERE table_name = %s
                """,
                [self.normalize_name(table_name)],
            )
            return cursor.fetchone()[0]