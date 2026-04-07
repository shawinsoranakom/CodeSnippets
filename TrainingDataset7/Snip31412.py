def _test_composed_constraint_with_fk(self, constraint):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(Book)
        table = Book._meta.db_table
        self.assertEqual(Book._meta.constraints, [])
        Book._meta.constraints = [constraint]
        with connection.schema_editor() as editor:
            editor.add_constraint(Book, constraint)
        self.assertIn(constraint.name, self.get_constraints(table))
        Book._meta.constraints = []
        with connection.schema_editor() as editor:
            editor.remove_constraint(Book, constraint)
        self.assertNotIn(constraint.name, self.get_constraints(table))