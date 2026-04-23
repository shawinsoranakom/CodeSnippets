def test_dependency_sorting_m2m_complex_circular_2(self):
        """
        Circular M2M relations with explicit through models should be
        serializable This test tests the circularity with explicit
        natural_key.dependencies
        """
        sorted_deps = serializers.sort_dependencies(
            [
                (
                    "fixtures_regress",
                    [M2MComplexCircular2A, M2MComplexCircular2B, M2MCircular2ThroughAB],
                )
            ]
        )
        self.assertEqual(sorted_deps[:2], [M2MComplexCircular2A, M2MComplexCircular2B])
        self.assertEqual(sorted_deps[2:], [M2MCircular2ThroughAB])