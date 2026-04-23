def test_register_non_serializer(self):
        with self.assertRaisesMessage(
            ValueError, "'TestModel1' must inherit from 'BaseSerializer'."
        ):
            MigrationWriter.register_serializer(complex, TestModel1)