def test_create_model_and_remove_model_options(self):
        self.assertOptimizesTo(
            [
                migrations.CreateModel(
                    "MyModel",
                    fields=[],
                    options={"verbose_name": "My Model"},
                ),
                migrations.AlterModelOptions("MyModel", options={}),
            ],
            [migrations.CreateModel("MyModel", fields=[])],
        )
        self.assertOptimizesTo(
            [
                migrations.CreateModel(
                    "MyModel",
                    fields=[],
                    options={
                        "verbose_name": "My Model",
                        "verbose_name_plural": "My Model plural",
                    },
                ),
                migrations.AlterModelOptions(
                    "MyModel",
                    options={"verbose_name": "My Model"},
                ),
            ],
            [
                migrations.CreateModel(
                    "MyModel",
                    fields=[],
                    options={"verbose_name": "My Model"},
                ),
            ],
        )