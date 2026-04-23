def test_unique_constraint_index_nulls_distinct(self):
        """
        For a UniqueConstraint with expressions, the backend executes:
        CREATE UNIQUE INDEX ...
        """
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        nulls_distinct = UniqueConstraint(
            F("height"), name="distinct_height", nulls_distinct=True
        )
        nulls_not_distinct = UniqueConstraint(
            F("weight"), name="not_distinct_weight", nulls_distinct=False
        )
        with connection.schema_editor() as editor:
            editor.add_constraint(Author, nulls_distinct)
            editor.add_constraint(Author, nulls_not_distinct)
        Author.objects.create(name="", height=None, weight=None)
        Author.objects.create(name="", height=None, weight=1)
        with self.assertRaises(IntegrityError):
            Author.objects.create(name="", height=1, weight=None)
        with connection.schema_editor() as editor:
            editor.remove_constraint(Author, nulls_distinct)
            editor.remove_constraint(Author, nulls_not_distinct)
        constraints = self.get_constraints(Author._meta.db_table)
        self.assertNotIn(nulls_distinct.name, constraints)
        self.assertNotIn(nulls_not_distinct.name, constraints)