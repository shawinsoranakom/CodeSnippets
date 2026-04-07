def test_expression_wrapped_with_parentheses_on_postgresql(self):
        """
        The SQL for the Cast expression is wrapped with parentheses in case
        it's a complex expression.
        """
        with CaptureQueriesContext(connection) as captured_queries:
            list(
                Author.objects.annotate(
                    cast_float=Cast(models.Avg("age"), models.FloatField()),
                )
            )
        self.assertIn(
            '(AVG("db_functions_author"."age"))::double precision',
            captured_queries[0]["sql"],
        )