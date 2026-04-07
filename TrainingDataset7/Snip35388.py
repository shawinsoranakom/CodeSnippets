def test_match(self):
        self.__class__.databases = {"default", "other"}
        self.assertEqual(self._validate_databases(), frozenset({"default", "other"}))