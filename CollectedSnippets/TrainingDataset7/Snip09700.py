def get_relations(self, cursor, table_name):
        """
        Return a dictionary of
            {
                field_name: (field_name_other_table, other_table, db_on_delete)
            }
        representing all foreign keys in the given table.
        """
        table_name = table_name.upper()
        cursor.execute(
            """
    SELECT ca.column_name, cb.table_name, cb.column_name, user_constraints.delete_rule
    FROM   user_constraints, USER_CONS_COLUMNS ca, USER_CONS_COLUMNS cb
    WHERE  user_constraints.table_name = %s AND
           user_constraints.constraint_name = ca.constraint_name AND
           user_constraints.r_constraint_name = cb.constraint_name AND
           ca.position = cb.position""",
            [table_name],
        )

        return {
            self.identifier_converter(field_name): (
                self.identifier_converter(rel_field_name),
                self.identifier_converter(rel_table_name),
                self.on_delete_types.get(on_delete),
            )
            for (
                field_name,
                rel_table_name,
                rel_field_name,
                on_delete,
            ) in cursor.fetchall()
        }