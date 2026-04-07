def test_dependency_sorting_long(self):
        with self.assertRaisesMessage(
            RuntimeError,
            "Can't resolve dependencies for fixtures_regress.Circle1, "
            "fixtures_regress.Circle2, fixtures_regress.Circle3 in serialized "
            "app list.",
        ):
            serializers.sort_dependencies(
                [("fixtures_regress", [Person, Circle2, Circle1, Circle3, Store, Book])]
            )