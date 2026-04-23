def test_alter_remove_constraint(self):
        self.assertOptimizesTo(
            [
                migrations.AlterConstraint(
                    "Pony",
                    "pink_gt_2",
                    models.CheckConstraint(
                        condition=models.Q(pink__gt=2), name="pink_gt_2"
                    ),
                ),
                migrations.RemoveConstraint("Pony", "pink_gt_2"),
            ],
            [migrations.RemoveConstraint("Pony", "pink_gt_2")],
        )