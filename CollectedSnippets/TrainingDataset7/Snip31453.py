def test_func_index_unsupported(self):
        # Index is ignored on databases that don't support indexes on
        # expressions.
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        index = Index(F("name"), name="random_idx")
        with connection.schema_editor() as editor, self.assertNumQueries(0):
            self.assertIsNone(editor.add_index(Author, index))
            self.assertIsNone(editor.remove_index(Author, index))