def test_serialize_builtins(self):
        string, imports = MigrationWriter.serialize(range)
        self.assertEqual(string, "range")
        self.assertEqual(imports, set())