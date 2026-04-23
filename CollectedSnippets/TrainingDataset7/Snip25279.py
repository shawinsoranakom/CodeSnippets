def test_get_relations(self):
        with connection.cursor() as cursor:
            relations = connection.introspection.get_relations(
                cursor, Article._meta.db_table
            )

        if connection.vendor == "mysql" and connection.mysql_is_mariadb:
            no_db_on_delete = None
        else:
            no_db_on_delete = DO_NOTHING
        # {field_name: (field_name_other_table, other_table, db_on_delete)}
        expected_relations = {
            "reporter_id": ("id", Reporter._meta.db_table, no_db_on_delete),
            "response_to_id": ("id", Article._meta.db_table, no_db_on_delete),
        }
        self.assertEqual(relations, expected_relations)

        # Removing a field shouldn't disturb get_relations (#17785)
        body = Article._meta.get_field("body")
        with connection.schema_editor() as editor:
            editor.remove_field(Article, body)
        with connection.cursor() as cursor:
            relations = connection.introspection.get_relations(
                cursor, Article._meta.db_table
            )
        with connection.schema_editor() as editor:
            editor.add_field(Article, body)
        self.assertEqual(relations, expected_relations)