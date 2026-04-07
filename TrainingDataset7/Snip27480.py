def _get_column_id_type(cursor, table, column):
            return [
                c.type_code
                for c in connection.introspection.get_table_description(
                    cursor,
                    f"{app_label}_{table}",
                )
                if c.name == column
            ][0]