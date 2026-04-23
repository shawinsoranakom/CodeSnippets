def test_adding_arrayfield_with_index(self):
        """
        ArrayField shouldn't have varchar_patterns_ops or text_patterns_ops
        indexes.
        """
        table_name = "postgres_tests_chartextarrayindexmodel"
        call_command("migrate", "postgres_tests", verbosity=0)
        with connection.cursor() as cursor:
            like_constraint_columns_list = [
                v["columns"]
                for k, v in list(
                    connection.introspection.get_constraints(cursor, table_name).items()
                )
                if k.endswith("_like")
            ]
        # Only the CharField should have a LIKE index.
        self.assertEqual(like_constraint_columns_list, [["char2"]])
        # All fields should have regular indexes.
        with connection.cursor() as cursor:
            indexes = [
                c["columns"][0]
                for c in connection.introspection.get_constraints(
                    cursor, table_name
                ).values()
                if c["index"] and len(c["columns"]) == 1
            ]
        self.assertIn("char", indexes)
        self.assertIn("char2", indexes)
        self.assertIn("text", indexes)
        call_command("migrate", "postgres_tests", "zero", verbosity=0)
        with connection.cursor() as cursor:
            self.assertNotIn(table_name, connection.introspection.table_names(cursor))