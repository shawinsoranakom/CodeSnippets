def test_create_model_alter_constraint(self):
        original_constraint = models.CheckConstraint(
            condition=models.Q(weight__gt=0), name="pony_weight_gt_0"
        )
        altered_constraint = models.CheckConstraint(
            condition=models.Q(weight__gt=0),
            name="pony_weight_gt_0",
            violation_error_message="incorrect weight",
        )
        self.assertOptimizesTo(
            [
                migrations.CreateModel(
                    name="Pony",
                    fields=[
                        ("weight", models.IntegerField()),
                    ],
                    options={
                        "constraints": [
                            original_constraint,
                            models.UniqueConstraint(
                                "weight", name="pony_weight_unique"
                            ),
                        ],
                    },
                ),
                migrations.AlterConstraint(
                    "Pony", "pony_weight_gt_0", altered_constraint
                ),
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
                                "weight",
                                name="pony_weight_unique",
                            ),
                            altered_constraint,
                        ]
                    },
                ),
            ],
        )