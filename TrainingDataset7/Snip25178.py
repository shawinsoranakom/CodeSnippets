def test_index_name(self):
        """
        Index names on the built-in database backends::
            * Are truncated as needed.
            * Include all the column names.
            * Include a deterministic hash.
        """
        long_name = "l%sng" % ("o" * 100)
        editor = connection.schema_editor()
        index_name = editor._create_index_name(
            table_name=Article._meta.db_table,
            column_names=("c1", "c2", long_name),
            suffix="ix",
        )
        expected = {
            "mysql": "indexes_article_c1_c2_looooooooooooooooooo_255179b2ix",
            "oracle": "indexes_a_c1_c2_loo_255179b2ix",
            "postgresql": "indexes_article_c1_c2_loooooooooooooooooo_255179b2ix",
            "sqlite": "indexes_article_c1_c2_l%sng_255179b2ix" % ("o" * 100),
        }
        if connection.vendor not in expected:
            self.skipTest(
                "This test is only supported on the built-in database backends."
            )
        self.assertEqual(index_name, expected[connection.vendor])