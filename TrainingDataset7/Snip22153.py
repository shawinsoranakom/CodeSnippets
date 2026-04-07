def test_deeply_nested_elements(self):
        """Text inside deeply-nested tags raises SuspiciousOperation."""
        for file in [
            "invalid_deeply_nested_elements.xml",
            "invalid_deeply_nested_elements_natural_key.xml",
        ]:
            with self.subTest(file=file), self.assertRaises(SuspiciousOperation):
                management.call_command("loaddata", file, verbosity=0)