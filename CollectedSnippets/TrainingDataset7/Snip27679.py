def assertSerializedFunctoolsPartialEqual(
        self, value, expected_string, expected_imports
    ):
        string, imports = MigrationWriter.serialize(value)
        self.assertEqual(string, expected_string)
        self.assertEqual(imports, expected_imports)
        result = self.serialize_round_trip(value)
        self.assertEqual(result.func, value.func)
        self.assertEqual(result.args, value.args)
        self.assertEqual(result.keywords, value.keywords)
        return result