def test_index_name_hash(self):
        """
        Index names should be deterministic.
        """
        editor = connection.schema_editor()
        index_name = editor._create_index_name(
            table_name=Article._meta.db_table,
            column_names=("c1",),
            suffix="123",
        )
        self.assertEqual(index_name, "indexes_article_c1_a52bd80b123")