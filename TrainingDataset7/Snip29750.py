def test_table_create(self):
        constraint_name = "exclusion_equal_number_tc"

        class ModelWithExclusionConstraint(Model):
            number = IntegerField()

            class Meta:
                app_label = "postgres_tests"
                constraints = [
                    ExclusionConstraint(
                        name=constraint_name,
                        expressions=[("number", RangeOperators.EQUAL)],
                    )
                ]

        with connection.schema_editor() as editor:
            editor.create_model(ModelWithExclusionConstraint)
        self.assertIn(
            constraint_name,
            self.get_constraints(ModelWithExclusionConstraint._meta.db_table),
        )