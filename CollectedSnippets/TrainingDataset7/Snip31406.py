def _test_composed_index_with_fk(self, index):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(Book)
        table = Book._meta.db_table
        self.assertEqual(Book._meta.indexes, [])
        Book._meta.indexes = [index]
        with connection.schema_editor() as editor:
            editor.add_index(Book, index)
        self.assertIn(index.name, self.get_constraints(table))
        Book._meta.indexes = []
        with connection.schema_editor() as editor:
            editor.remove_index(Book, index)
        self.assertNotIn(index.name, self.get_constraints(table))