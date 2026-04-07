def test_create_model_remove_constraint(self):
        self.assertOptimizesTo(
            [
                migrations.CreateModel(
                    name="Pony",
                    fields=[
                        ("weight", models.IntegerField()),
                    ],
                    options={
                        "constraints": [
                            models.CheckConstraint(
                                condition=models.Q(weight__gt=0),
                                name="pony_weight_gt_0",
                            ),
                            models.UniqueConstraint(
                                "weight", name="pony_weight_unique"
                            ),
                        ],
                    },
                ),
                migrations.RemoveConstraint("Pony", "pony_weight_gt_0"),
            ],
            [
                migrations.CreateModel(
                    name="Pony",
                    fields=[
                        ("weight", models.IntegerField()),
                    ],
                    options={
                        "constraints": [
                            models.UniqueConstraint(
                                "weight", name="pony_weight_unique"
                            ),
                        ]
                    },
                ),
            ],
        )