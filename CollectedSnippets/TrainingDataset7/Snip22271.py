def test_dependency_sorting_5(self):
        sorted_deps = serializers.sort_dependencies(
            [("fixtures_regress", [Person, Book, Store])]
        )
        self.assertEqual(sorted_deps, [Store, Person, Book])