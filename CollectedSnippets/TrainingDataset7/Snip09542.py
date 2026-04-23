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
            SELECT
                kcu.column_name,
                kcu.referenced_column_name,
                kcu.referenced_table_name,
                rc.delete_rule
            FROM
                information_schema.key_column_usage kcu
            JOIN
                information_schema.referential_constraints rc
                ON rc.constraint_name = kcu.constraint_name
                AND rc.constraint_schema = kcu.constraint_schema
            WHERE kcu.table_name = %s
                AND kcu.table_schema = DATABASE()
                AND kcu.referenced_table_schema = DATABASE()
                AND kcu.referenced_table_name IS NOT NULL
                AND kcu.referenced_column_name IS NOT NULL
            """,
            [table_name],
        )
        return {
            field_name: (other_field, other_table, self.on_delete_types.get(on_delete))
            for field_name, other_field, other_table, on_delete in cursor.fetchall()
        }