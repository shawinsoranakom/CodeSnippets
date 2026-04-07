def get_sequences(self, cursor, table_name, table_fields=()):
        cursor.execute(
            """
            SELECT
                user_tab_identity_cols.sequence_name,
                user_tab_identity_cols.column_name
            FROM
                user_tab_identity_cols,
                user_constraints,
                user_cons_columns cols
            WHERE
                user_constraints.constraint_name = cols.constraint_name
                AND user_constraints.table_name = user_tab_identity_cols.table_name
                AND cols.column_name = user_tab_identity_cols.column_name
                AND user_constraints.constraint_type = 'P'
                AND user_tab_identity_cols.table_name = UPPER(%s)
            """,
            [table_name],
        )
        # Oracle allows only one identity column per table.
        row = cursor.fetchone()
        if row:
            return [
                {
                    "name": self.identifier_converter(row[0]),
                    "table": self.identifier_converter(table_name),
                    "column": self.identifier_converter(row[1]),
                }
            ]
        # To keep backward compatibility for AutoFields that aren't Oracle
        # identity columns.
        for f in table_fields:
            if isinstance(f, models.AutoField):
                return [{"table": table_name, "column": f.column}]
        return []