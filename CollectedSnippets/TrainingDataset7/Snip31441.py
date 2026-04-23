def test_func_index(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        index = Index(Lower("name").desc(), name="func_lower_idx")
        # Add index.
        with connection.schema_editor() as editor:
            editor.add_index(Author, index)
            sql = index.create_sql(Author, editor)
        table = Author._meta.db_table
        if connection.features.supports_index_column_ordering:
            self.assertIndexOrder(table, index.name, ["DESC"])
        # SQL contains a database function.
        self.assertIs(sql.references_column(table, "name"), True)
        self.assertIn("LOWER(%s)" % editor.quote_name("name"), str(sql))
        # Remove index.
        with connection.schema_editor() as editor:
            editor.remove_index(Author, index)
        self.assertNotIn(index.name, self.get_constraints(table))