def assertJSONEqual(self, a, b):
        """Asserts that two JSON dicts are equal. If either arg is a string,
        it will be first converted to a dict with json.loads()."""
        # Ensure both objects are dicts.
        dict_a = a if isinstance(a, dict) else json.loads(a)
        dict_b = b if isinstance(b, dict) else json.loads(b)
        self.assertEqual(dict_a, dict_b)