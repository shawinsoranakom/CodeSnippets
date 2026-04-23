def test_dependency_self_referential(self):
        with self.assertRaisesMessage(
            RuntimeError,
            "Can't resolve dependencies for fixtures_regress.Circle3 in "
            "serialized app list.",
        ):
            serializers.sort_dependencies([("fixtures_regress", [Book, Circle3])])