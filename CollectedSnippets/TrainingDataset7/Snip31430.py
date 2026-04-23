def test_unique_constraint_nulls_distinct_unsupported(self):
        # UniqueConstraint is ignored on databases that don't support
        # NULLS [NOT] DISTINCT.
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        constraint = UniqueConstraint(
            F("name"), name="func_name_uq", nulls_distinct=True
        )
        with connection.schema_editor() as editor, self.assertNumQueries(0):
            self.assertIsNone(editor.add_constraint(Author, constraint))
            self.assertIsNone(editor.remove_constraint(Author, constraint))