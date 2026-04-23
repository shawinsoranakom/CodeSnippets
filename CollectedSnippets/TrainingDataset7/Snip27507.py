def test_create_alter_owrt_delete_model(self):
        self._test_create_alter_foo_delete_model(
            migrations.AlterOrderWithRespectTo("Foo", "a")
        )