def test_create_alter_index_field(self):
        self._test_create_alter_foo_field(
            migrations.AlterIndexTogether("Foo", [["a", "b"]])
        )