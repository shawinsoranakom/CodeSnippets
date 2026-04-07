def test_dependency_sorting_normal(self):
        sorted_deps = serializers.sort_dependencies(
            [("fixtures_regress", [Person, ExternalDependency, Book])]
        )
        self.assertEqual(sorted_deps, [Person, Book, ExternalDependency])