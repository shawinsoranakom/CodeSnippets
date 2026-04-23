def test_create_alter_model_managers(self):
        self.assertOptimizesTo(
            [
                migrations.CreateModel("Foo", fields=[]),
                migrations.AlterModelManagers(
                    name="Foo",
                    managers=[
                        ("objects", models.Manager()),
                        ("things", models.Manager()),
                    ],
                ),
            ],
            [
                migrations.CreateModel(
                    "Foo",
                    fields=[],
                    managers=[
                        ("objects", models.Manager()),
                        ("things", models.Manager()),
                    ],
                ),
            ],
        )