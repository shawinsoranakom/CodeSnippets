def test_unique_constraint_nulls_distinct_condition(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        constraint = UniqueConstraint(
            fields=["height", "weight"],
            name="un_height_weight_start_A",
            condition=Q(name__startswith="A"),
            nulls_distinct=False,
        )
        with connection.schema_editor() as editor:
            editor.add_constraint(Author, constraint)
        Author.objects.create(name="Adam", height=None, weight=None)
        Author.objects.create(name="Avocado", height=1, weight=None)
        Author.objects.create(name="Adrian", height=None, weight=1)
        with self.assertRaises(IntegrityError):
            Author.objects.create(name="Alex", height=None, weight=None)
        Author.objects.create(name="Bob", height=None, weight=None)
        with self.assertRaises(IntegrityError):
            Author.objects.create(name="Alex", height=1, weight=None)
        Author.objects.create(name="Bill", height=None, weight=None)
        with self.assertRaises(IntegrityError):
            Author.objects.create(name="Alex", height=None, weight=1)
        Author.objects.create(name="Celine", height=None, weight=1)
        with connection.schema_editor() as editor:
            editor.remove_constraint(Author, constraint)
        constraints = self.get_constraints(Author._meta.db_table)
        self.assertNotIn(constraint.name, constraints)