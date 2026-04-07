def test_dependency_sorting_2(self):
        sorted_deps = serializers.sort_dependencies(
            [("fixtures_regress", [Book, Store, Person])]
        )
        self.assertEqual(sorted_deps, [Store, Person, Book])