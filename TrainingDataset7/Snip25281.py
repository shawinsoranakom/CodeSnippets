def test_get_relations_db_on_delete_null(self):
        with connection.cursor() as cursor:
            relations = connection.introspection.get_relations(
                cursor, DbOnDeleteSetNullModel._meta.db_table
            )

        # {field_name: (field_name_other_table, other_table, db_on_delete)}
        expected_relations = {
            "fk_set_null_id": ("id", Reporter._meta.db_table, DB_SET_NULL),
        }
        self.assertEqual(relations, expected_relations)