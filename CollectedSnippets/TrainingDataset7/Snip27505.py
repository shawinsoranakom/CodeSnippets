def test_create_alter_unique_delete_model(self):
        self._test_create_alter_foo_delete_model(
            migrations.AlterUniqueTogether("Foo", [["a", "b"]])
        )