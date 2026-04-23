def test_literals_not_treated_as_expressions(self):
        """
        DatabaseFeatures.supports_expression_defaults = False shouldn't
        prevent non-expression literals (integer, float, boolean, etc.) from
        being used as database defaults.
        """

        class Model(models.Model):
            field = models.FloatField(db_default=1.0)

        field = Model._meta.get_field("field")
        with unittest.mock.patch.object(
            connection.features, "supports_expression_defaults", False
        ):
            errors = field.check(databases=self.databases)
        self.assertEqual(errors, [])