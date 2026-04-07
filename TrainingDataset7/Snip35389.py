def test_all(self):
        self.__class__.databases = "__all__"
        self.assertEqual(self._validate_databases(), frozenset(connections))