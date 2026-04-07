def test_custom_normalize_table_name(self):
        def pascal_case_table_only(table_name):
            return table_name.startswith("inspectdb_pascal")

        class MyCommand(inspectdb.Command):
            def normalize_table_name(self, table_name):
                normalized_name = table_name.split(".")[1]
                if connection.features.ignores_table_name_case:
                    normalized_name = normalized_name.lower()
                return normalized_name

        out = StringIO()
        call_command(MyCommand(), table_name_filter=pascal_case_table_only, stdout=out)
        if connection.features.ignores_table_name_case:
            expected_model_name = "pascalcase"
        else:
            expected_model_name = "PascalCase"
        self.assertIn(f"class {expected_model_name}(models.Model):", out.getvalue())