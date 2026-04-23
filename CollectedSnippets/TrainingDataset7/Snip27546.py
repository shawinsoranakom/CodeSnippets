def test_create_model_add_constraint(self):
        gt_constraint = models.CheckConstraint(
            condition=models.Q(weight__gt=0), name="pony_weight_gt_0"
        )
        self.assertOptimizesTo(
            [
                migrations.CreateModel(
                    name="Pony",
                    fields=[
                        ("weight", models.IntegerField()),
                    ],
                ),
                migrations.AddConstraint("Pony", gt_constraint),
            ],
            [
                migrations.CreateModel(
                    name="Pony",
                    fields=[
                        ("weight", models.IntegerField()),
                    ],
                    options={"constraints": [gt_constraint]},
                ),
            ],
        )