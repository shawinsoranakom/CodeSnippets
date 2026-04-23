def test_dependency_sorting_3(self):
        sorted_deps = serializers.sort_dependencies(
            [("fixtures_regress", [Store, Book, Person])]
        )
        self.assertEqual(sorted_deps, [Store, Person, Book])