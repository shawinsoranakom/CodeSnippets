def test_exclusion_constraint(self):
        class ExclusionModel(PostgreSQLModel):
            value = models.IntegerField()

            class Meta:
                constraints = [
                    ExclusionConstraint(
                        name="exclude_equal",
                        expressions=[("value", RangeOperators.EQUAL)],
                    )
                ]

        self.assert_model_check_errors(
            ExclusionModel, [self._make_error(ExclusionModel, "ExclusionConstraint")]
        )