def test_get_placeholder_deprecation(self):
        # RemovedInDjango70Warning: When the deprecation ends, remove
        # completely.
        msg = (
            "Field.get_placeholder is deprecated in favor of get_placeholder_sql. "
            "Define model_fields.tests.BasicFieldTests."
            "test_get_placeholder_deprecation.<locals>.SomeField.get_placeholder_sql "
            "to return both SQL and parameters instead."
        )
        with self.assertWarnsMessage(RemovedInDjango70Warning, msg):

            class SomeField(models.Field):
                def get_placeholder(self, value, compiler, connection):
                    return "%s"