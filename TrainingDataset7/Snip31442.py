def test_func_index_f(self):
        with connection.schema_editor() as editor:
            editor.create_model(Tag)
        index = Index("slug", F("title").desc(), name="func_f_idx")
        # Add index.
        with connection.schema_editor() as editor:
            editor.add_index(Tag, index)
            sql = index.create_sql(Tag, editor)
        table = Tag._meta.db_table
        self.assertIn(index.name, self.get_constraints(table))
        if connection.features.supports_index_column_ordering:
            self.assertIndexOrder(Tag._meta.db_table, index.name, ["ASC", "DESC"])
        # SQL contains columns.
        self.assertIs(sql.references_column(table, "slug"), True)
        self.assertIs(sql.references_column(table, "title"), True)
        # Remove index.
        with connection.schema_editor() as editor:
            editor.remove_index(Tag, index)
        self.assertNotIn(index.name, self.get_constraints(table))