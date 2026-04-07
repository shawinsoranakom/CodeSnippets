def test_func_unique_constraint_nondeterministic(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        constraint = UniqueConstraint(Random(), name="func_random_uq")
        with connection.schema_editor() as editor:
            with self.assertRaises(DatabaseError):
                editor.add_constraint(Author, constraint)