def _is_collation_deterministic(self, collation_name):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT collisdeterministic
                FROM pg_collation
                WHERE collname = %s
                """,
                [collation_name],
            )
            row = cursor.fetchone()
            return row[0] if row else None