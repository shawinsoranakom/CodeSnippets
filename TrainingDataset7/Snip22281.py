def test_dependency_sorting_m2m_simple(self):
        """
        M2M relations without explicit through models SHOULD count as
        dependencies

        Regression test for bugs that could be caused by flawed fixes to
        #14226, namely if M2M checks are removed from sort_dependencies
        altogether.
        """
        sorted_deps = serializers.sort_dependencies(
            [("fixtures_regress", [M2MSimpleA, M2MSimpleB])]
        )
        self.assertEqual(sorted_deps, [M2MSimpleB, M2MSimpleA])