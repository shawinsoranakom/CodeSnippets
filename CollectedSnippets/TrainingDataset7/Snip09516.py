def django_test_skips(self):
        skips = {
            "This doesn't work on MySQL.": {
                "db_functions.comparison.test_greatest.GreatestTests."
                "test_coalesce_workaround",
                "db_functions.comparison.test_least.LeastTests."
                "test_coalesce_workaround",
            },
            "MySQL doesn't support functional indexes on a function that "
            "returns JSON": {
                "schema.tests.SchemaTests.test_func_index_json_key_transform",
            },
            "MySQL supports multiplying and dividing DurationFields by a "
            "scalar value but it's not implemented (#25287).": {
                "expressions.tests.FTimeDeltaTests.test_durationfield_multiply_divide",
            },
            "UPDATE ... ORDER BY syntax on MySQL/MariaDB does not support ordering by"
            "related fields.": {
                "update.tests.AdvancedTests."
                "test_update_ordered_by_inline_m2m_annotation",
                "update.tests.AdvancedTests.test_update_ordered_by_m2m_annotation",
                "update.tests.AdvancedTests.test_update_ordered_by_m2m_annotation_desc",
            },
        }
        if not self.connection.mysql_is_mariadb:
            skips.update(
                {
                    "MySQL doesn't allow renaming columns referenced by generated "
                    "columns": {
                        "migrations.test_operations.OperationTests."
                        "test_invalid_generated_field_changes_on_rename_stored",
                        "migrations.test_operations.OperationTests."
                        "test_invalid_generated_field_changes_on_rename_virtual",
                    },
                }
            )
        return skips