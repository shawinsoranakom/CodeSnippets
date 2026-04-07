def test_func_index_lookups(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        with register_lookup(CharField, Lower), register_lookup(IntegerField, Abs):
            index = Index(
                F("name__lower"),
                F("weight__abs"),
                name="func_lower_abs_lookup_idx",
            )
            # Add index.
            with connection.schema_editor() as editor:
                editor.add_index(Author, index)
                sql = index.create_sql(Author, editor)
        table = Author._meta.db_table
        self.assertIn(index.name, self.get_constraints(table))
        # SQL contains columns.
        self.assertIs(sql.references_column(table, "name"), True)
        self.assertIs(sql.references_column(table, "weight"), True)
        # Remove index.
        with connection.schema_editor() as editor:
            editor.remove_index(Author, index)
        self.assertNotIn(index.name, self.get_constraints(table))