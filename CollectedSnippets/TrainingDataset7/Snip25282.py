def test_get_relations_db_on_delete_default(self):
        with connection.cursor() as cursor:
            relations = connection.introspection.get_relations(
                cursor, DbOnDeleteSetDefaultModel._meta.db_table
            )

        # {field_name: (field_name_other_table, other_table, db_on_delete)}
        expected_relations = {
            "fk_db_set_default_id": ("id", Country._meta.db_table, DB_SET_DEFAULT),
        }
        self.assertEqual(relations, expected_relations)