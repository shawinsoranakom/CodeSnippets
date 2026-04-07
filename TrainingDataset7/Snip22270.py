def test_dependency_sorting_4(self):
        sorted_deps = serializers.sort_dependencies(
            [("fixtures_regress", [Store, Person, Book])]
        )
        self.assertEqual(sorted_deps, [Store, Person, Book])