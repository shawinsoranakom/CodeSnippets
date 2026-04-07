def test_get_relations_db_on_delete_cascade(self):
        with connection.cursor() as cursor:
            relations = connection.introspection.get_relations(
                cursor, DbOnDeleteCascadeModel._meta.db_table
            )

        if connection.vendor == "mysql" and connection.mysql_is_mariadb:
            no_db_on_delete = None
        else:
            no_db_on_delete = DO_NOTHING
        # {field_name: (field_name_other_table, other_table, db_on_delete)}
        expected_relations = {
            "fk_db_cascade_id": ("id", City._meta.db_table, DB_CASCADE),
            "fk_do_nothing_id": ("id", Country._meta.db_table, no_db_on_delete),
        }
        self.assertEqual(relations, expected_relations)