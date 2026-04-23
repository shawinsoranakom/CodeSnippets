def test_dependency_sorting(self):
        """
        It doesn't matter what order you mention the models, Store *must* be
        serialized before then Person, and both must be serialized before Book.
        """
        sorted_deps = serializers.sort_dependencies(
            [("fixtures_regress", [Book, Person, Store])]
        )
        self.assertEqual(sorted_deps, [Store, Person, Book])