def get_relations(self, cursor, table_name):
        """
        Return a dictionary of
            {column_name: (ref_column_name, ref_table_name, db_on_delete)}
        representing all foreign keys in the given table.
        """
        cursor.execute(
            "PRAGMA foreign_key_list(%s)" % self.connection.ops.quote_name(table_name)
        )
        return {
            column_name: (
                ref_column_name,
                ref_table_name,
                self.on_delete_types.get(on_delete),
            )
            for (
                _,
                _,
                ref_table_name,
                column_name,
                ref_column_name,
                _,
                on_delete,
                *_,
            ) in cursor.fetchall()
        }