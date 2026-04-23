def test_create_model_remove_index(self):
        self.assertOptimizesTo(
            [
                migrations.CreateModel(
                    name="Pony",
                    fields=[
                        ("weight", models.IntegerField()),
                        ("age", models.IntegerField()),
                    ],
                    options={
                        "indexes": [
                            models.Index(fields=["age"], name="idx_pony_age"),
                            models.Index(fields=["weight"], name="idx_pony_weight"),
                        ],
                    },
                ),
                migrations.RemoveIndex("Pony", "idx_pony_age"),
            ],
            [
                migrations.CreateModel(
                    name="Pony",
                    fields=[
                        ("weight", models.IntegerField()),
                        ("age", models.IntegerField()),
                    ],
                    options={
                        "indexes": [
                            models.Index(fields=["weight"], name="idx_pony_weight"),
                        ],
                    },
                ),
            ],
        )