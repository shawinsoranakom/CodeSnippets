def test_create_alter_model_table_comment(self):
        self.assertOptimizesTo(
            [
                migrations.CreateModel("Foo", fields=[]),
                migrations.AlterModelTableComment(
                    name="foo",
                    table_comment="A lovely table.",
                ),
            ],
            [
                migrations.CreateModel(
                    "Foo",
                    fields=[],
                    options={
                        "db_table_comment": "A lovely table.",
                    },
                ),
            ],
        )