def test_quoted_index_name(self):
        editor = connection.schema_editor()
        index_sql = [str(statement) for statement in editor._model_indexes_sql(Article)]
        self.assertEqual(len(index_sql), 1)
        # Ensure the index name is properly quoted.
        self.assertIn(
            connection.ops.quote_name(Article._meta.indexes[0].name),
            index_sql[0],
        )