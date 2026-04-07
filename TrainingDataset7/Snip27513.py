def test_alter_alter_field(self):
        self._test_alter_alter(
            migrations.AlterField("Foo", "name", models.IntegerField()),
            migrations.AlterField("Foo", "name", models.IntegerField(help_text="help")),
        )