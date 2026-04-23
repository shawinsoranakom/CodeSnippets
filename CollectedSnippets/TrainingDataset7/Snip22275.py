def test_dependency_sorting_tight_circular_2(self):
        with self.assertRaisesMessage(
            RuntimeError,
            "Can't resolve dependencies for fixtures_regress.Circle1, "
            "fixtures_regress.Circle2 in serialized app list.",
        ):
            serializers.sort_dependencies(
                [("fixtures_regress", [Circle1, Book, Circle2])]
            )