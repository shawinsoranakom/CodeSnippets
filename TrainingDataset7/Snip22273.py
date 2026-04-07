def test_dependency_sorting_dangling(self):
        sorted_deps = serializers.sort_dependencies(
            [("fixtures_regress", [Person, Circle1, Store, Book])]
        )
        self.assertEqual(sorted_deps, [Circle1, Store, Person, Book])