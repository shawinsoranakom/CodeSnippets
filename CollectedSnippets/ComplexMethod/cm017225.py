def get_table_description(self, cursor, table_name):
        """
        Return a description of the table with the DB-API cursor.description
        interface.
        """
        cursor.execute(
            "PRAGMA table_xinfo(%s)" % self.connection.ops.quote_name(table_name)
        )
        table_info = cursor.fetchall()
        if not table_info:
            raise DatabaseError(f"Table {table_name} does not exist (empty pragma).")
        collations = self._get_column_collations(cursor, table_name)
        json_columns = set()
        if self.connection.features.can_introspect_json_field:
            for line in table_info:
                column = line[1]
                json_constraint_sql = '%%json_valid("%s")%%' % column
                has_json_constraint = cursor.execute(
                    """
                    SELECT sql
                    FROM sqlite_master
                    WHERE
                        type = 'table' AND
                        name = %s AND
                        sql LIKE %s
                """,
                    [table_name, json_constraint_sql],
                ).fetchone()
                if has_json_constraint:
                    json_columns.add(column)
        table_description = [
            FieldInfo(
                name,
                data_type,
                get_field_size(data_type),
                None,
                None,
                None,
                not notnull,
                default,
                collations.get(name),
                bool(pk),
                name in json_columns,
            )
            for cid, name, data_type, notnull, default, pk, hidden in table_info
            if hidden
            in [
                0,  # Normal column.
                2,  # Virtual generated column.
                3,  # Stored generated column.
            ]
        ]
        # If the primary key is composed of multiple columns they should not
        # be individually marked as pk.
        primary_key = [
            index for index, field_info in enumerate(table_description) if field_info.pk
        ]
        if len(primary_key) > 1:
            for index in primary_key:
                table_description[index] = table_description[index]._replace(pk=False)
        return table_description