def get_primary_key_columns(self, cursor, table_name):
        cursor.execute(
            """
            SELECT
                cols.column_name
            FROM
                user_constraints,
                user_cons_columns cols
            WHERE
                user_constraints.constraint_name = cols.constraint_name AND
                user_constraints.constraint_type = 'P' AND
                user_constraints.table_name = UPPER(%s)
            ORDER BY
                cols.position
            """,
            [table_name],
        )
        return [self.identifier_converter(row[0]) for row in cursor.fetchall()]