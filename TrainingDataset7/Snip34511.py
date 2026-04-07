def test_string_origin(self):
        template = self._engine().from_string("string template")
        self.assertEqual(template.origin.name, UNKNOWN_SOURCE)
        self.assertIsNone(template.origin.loader_name)
        self.assertEqual(template.source, "string template")