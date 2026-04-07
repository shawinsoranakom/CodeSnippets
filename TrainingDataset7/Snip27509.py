def test_alter_alter_table_model(self):
        self._test_alter_alter(
            migrations.AlterModelTable("Foo", "a"),
            migrations.AlterModelTable("Foo", "b"),
        )