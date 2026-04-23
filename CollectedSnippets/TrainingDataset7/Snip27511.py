def test_alter_alter_index_model(self):
        self._test_alter_alter(
            migrations.AlterIndexTogether("Foo", [["a", "b"]]),
            migrations.AlterIndexTogether("Foo", [["a", "c"]]),
        )