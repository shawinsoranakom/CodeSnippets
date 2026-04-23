def test_dependency_sorting_m2m_complex_circular_1(self):
        """
        Circular M2M relations with explicit through models should be
        serializable
        """
        A, B, C, AtoB, BtoC, CtoA = (
            M2MComplexCircular1A,
            M2MComplexCircular1B,
            M2MComplexCircular1C,
            M2MCircular1ThroughAB,
            M2MCircular1ThroughBC,
            M2MCircular1ThroughCA,
        )
        sorted_deps = serializers.sort_dependencies(
            [("fixtures_regress", [A, B, C, AtoB, BtoC, CtoA])]
        )
        # The dependency sorting should not result in an error, and the
        # through model should have dependencies to the other models and as
        # such come last in the list.
        self.assertEqual(sorted_deps[:3], [A, B, C])
        self.assertEqual(sorted_deps[3:], [AtoB, BtoC, CtoA])