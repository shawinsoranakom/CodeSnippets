def test_unique_constraint_nulls_distinct(self):
        """
        For UniqueConstraint(fields=...), the backend executes:
        ALTER TABLE "schema_author" ADD CONSTRAINT ...
        """
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        constraint = UniqueConstraint(
            fields=["height", "weight"], name="constraint", nulls_distinct=False
        )
        with connection.schema_editor() as editor:
            editor.add_constraint(Author, constraint)
        Author.objects.create(name="", height=None, weight=None)
        Author.objects.create(name="", height=1, weight=None)
        Author.objects.create(name="", height=None, weight=1)
        with self.assertRaises(IntegrityError):
            Author.objects.create(name="", height=None, weight=None)
        with self.assertRaises(IntegrityError):
            Author.objects.create(name="", height=1, weight=None)
        with self.assertRaises(IntegrityError):
            Author.objects.create(name="", height=None, weight=1)
        with connection.schema_editor() as editor:
            editor.remove_constraint(Author, constraint)
        constraints = self.get_constraints(Author._meta.db_table)
        self.assertNotIn(constraint.name, constraints)