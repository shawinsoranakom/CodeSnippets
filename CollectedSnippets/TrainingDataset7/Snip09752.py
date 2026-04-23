def _get_sequence_name(self, cursor, table, pk_name):
        cursor.execute(
            """
            SELECT sequence_name
            FROM user_tab_identity_cols
            WHERE table_name = UPPER(%s)
            AND column_name = UPPER(%s)""",
            [table, pk_name],
        )
        row = cursor.fetchone()
        return self._get_no_autofield_sequence_name(table) if row is None else row[0]