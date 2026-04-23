def test_check_constraint_raw_sql_check(self):
        class Model(models.Model):
            class Meta:
                required_db_features = {"supports_table_check_constraints"}
                constraints = [
                    models.CheckConstraint(
                        condition=models.Q(id__gt=0), name="q_check"
                    ),
                    models.CheckConstraint(
                        condition=models.ExpressionWrapper(
                            models.Q(price__gt=20),
                            output_field=models.BooleanField(),
                        ),
                        name="expression_wrapper_check",
                    ),
                    models.CheckConstraint(
                        condition=models.expressions.RawSQL(
                            "id = 0",
                            params=(),
                            output_field=models.BooleanField(),
                        ),
                        name="raw_sql_check",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.ExpressionWrapper(
                                models.Q(
                                    models.expressions.RawSQL(
                                        "id = 0",
                                        params=(),
                                        output_field=models.BooleanField(),
                                    )
                                ),
                                output_field=models.BooleanField(),
                            )
                        ),
                        name="nested_raw_sql_check",
                    ),
                ]

        expected_warnings = (
            [
                Warning(
                    "Check constraint 'raw_sql_check' contains RawSQL() expression and "
                    "won't be validated during the model full_clean().",
                    hint="Silence this warning if you don't care about it.",
                    obj=Model,
                    id="models.W045",
                ),
                Warning(
                    "Check constraint 'nested_raw_sql_check' contains RawSQL() "
                    "expression and won't be validated during the model full_clean().",
                    hint="Silence this warning if you don't care about it.",
                    obj=Model,
                    id="models.W045",
                ),
            ]
            if connection.features.supports_table_check_constraints
            else []
        )
        self.assertEqual(Model.check(databases=self.databases), expected_warnings)