def get_relations(self, cursor, table_name):
        """
        Return a dictionary of
            {
                field_name: (field_name_other_table, other_table, db_on_delete)
            }
        representing all foreign keys in the given table.
        """
        cursor.execute(
            """
            SELECT a1.attname, c2.relname, a2.attname, con.confdeltype
            FROM pg_constraint con
            LEFT JOIN pg_class c1 ON con.conrelid = c1.oid
            LEFT JOIN pg_class c2 ON con.confrelid = c2.oid
            LEFT JOIN
                pg_attribute a1 ON c1.oid = a1.attrelid AND a1.attnum = con.conkey[1]
            LEFT JOIN
                pg_attribute a2 ON c2.oid = a2.attrelid AND a2.attnum = con.confkey[1]
            WHERE
                c1.relname = %s AND
                con.contype = 'f' AND
                c1.relnamespace = c2.relnamespace AND
                pg_catalog.pg_table_is_visible(c1.oid)
        """,
            [table_name],
        )
        return {
            row[0]: (row[2], row[1], self.on_delete_types.get(row[3]))
            for row in cursor.fetchall()
        }