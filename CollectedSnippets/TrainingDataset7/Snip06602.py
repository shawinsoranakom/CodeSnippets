def django_test_skips(self):
        skips = super().django_test_skips
        skips.update(
            {
                "Oracle doesn't support spatial operators in constraints.": {
                    "gis_tests.gis_migrations.test_operations.OperationTests."
                    "test_add_check_constraint",
                },
            }
        )
        return skips