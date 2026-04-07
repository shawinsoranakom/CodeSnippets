def test_get_placeholder_sql_shim(self):
        # RemovedInDjango70Warning: When the deprecation ends, remove
        # completely.
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")

            class SomeField(models.Field):
                def get_placeholder(self, value, compiler, connection):
                    return "(1 + %s)"

        compiler = Bar.objects.all().query.get_compiler(connection=connection)
        self.assertEqual(
            SomeField().get_placeholder_sql(2, compiler, connection),
            ("(1 + %s)", (2,)),
        )
        self.assertEqual(
            SomeField().get_placeholder_sql(models.Value(2), compiler, connection),
            ("(1 + %s)", (2,)),
        )