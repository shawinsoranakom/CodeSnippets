def test_dependency_sorting_6(self):
        sorted_deps = serializers.sort_dependencies(
            [("fixtures_regress", [Person, Store, Book])]
        )
        self.assertEqual(sorted_deps, [Store, Person, Book])