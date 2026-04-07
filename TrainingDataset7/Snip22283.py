def test_dependency_sorting_m2m_complex(self):
        """
        M2M relations with explicit through models should NOT count as
        dependencies. The through model itself will have dependencies, though.
        """
        sorted_deps = serializers.sort_dependencies(
            [("fixtures_regress", [M2MComplexA, M2MComplexB, M2MThroughAB])]
        )
        # Order between M2MComplexA and M2MComplexB doesn't matter. The through
        # model has dependencies to them though, so it should come last.
        self.assertEqual(sorted_deps[-1], M2MThroughAB)