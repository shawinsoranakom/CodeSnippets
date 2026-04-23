def test_create_alter_model_table(self):
        self.assertOptimizesTo(
            [
                migrations.CreateModel("Foo", fields=[]),
                migrations.AlterModelTable(
                    name="foo",
                    table="foo",
                ),
            ],
            [
                migrations.CreateModel(
                    "Foo",
                    fields=[],
                    options={
                        "db_table": "foo",
                    },
                ),
            ],
        )