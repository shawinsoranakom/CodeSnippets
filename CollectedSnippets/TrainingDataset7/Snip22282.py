def test_dependency_sorting_m2m_simple_circular(self):
        """
        Resolving circular M2M relations without explicit through models should
        fail loudly
        """
        with self.assertRaisesMessage(
            RuntimeError,
            "Can't resolve dependencies for fixtures_regress.M2MSimpleCircularA, "
            "fixtures_regress.M2MSimpleCircularB in serialized app list.",
        ):
            serializers.sort_dependencies(
                [("fixtures_regress", [M2MSimpleCircularA, M2MSimpleCircularB])]
            )