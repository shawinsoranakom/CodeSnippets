def test_omit_cross_database_relations(self):
        default_connection = connections["default"]
        other_connection = connections["other"]
        main_table = "cross_schema_get_relations_main_table"
        main_table_quoted = default_connection.ops.quote_name(main_table)
        other_schema_quoted = other_connection.ops.quote_name(
            other_connection.settings_dict["NAME"]
        )
        rel_table = "cross_schema_get_relations_rel_table"
        rel_table_quoted = other_connection.ops.quote_name(rel_table)
        rel_column = "cross_schema_get_relations_rel_table_id"
        rel_column_quoted = other_connection.ops.quote_name(rel_column)
        try:
            with other_connection.cursor() as other_cursor:
                other_cursor.execute(f"""
                    CREATE TABLE {rel_table_quoted} (
                        id integer AUTO_INCREMENT,
                        PRIMARY KEY (id)
                    )
                    """)
            with default_connection.cursor() as default_cursor:
                # Create table in the default schema with a cross-database
                # relation.
                default_cursor.execute(f"""
                    CREATE TABLE {main_table_quoted} (
                        id integer AUTO_INCREMENT,
                        {rel_column_quoted} integer NOT NULL,
                        PRIMARY KEY (id),
                        FOREIGN KEY ({rel_column_quoted})
                        REFERENCES {other_schema_quoted}.{rel_table_quoted}(id)
                    )
                    """)
                relations = default_connection.introspection.get_relations(
                    default_cursor, main_table
                )
                constraints = default_connection.introspection.get_constraints(
                    default_cursor, main_table
                )
            self.assertEqual(len(relations), 0)
            rel_column_fk_constraints = [
                spec
                for name, spec in constraints.items()
                if spec["columns"] == [rel_column] and spec["foreign_key"] is not None
            ]
            self.assertEqual(len(rel_column_fk_constraints), 0)
        finally:
            with default_connection.cursor() as default_cursor:
                default_cursor.execute(f"DROP TABLE IF EXISTS {main_table_quoted}")
            with other_connection.cursor() as other_cursor:
                other_cursor.execute(f"DROP TABLE IF EXISTS {rel_table_quoted}")