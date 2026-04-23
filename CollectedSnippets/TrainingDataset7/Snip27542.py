def test_add_alter_constraint(self):
        constraint = models.CheckConstraint(
            condition=models.Q(pink__gt=2), name="pink_gt_2"
        )
        constraint_with_error = models.CheckConstraint(
            condition=models.Q(pink__gt=2),
            name="pink_gt_2",
            violation_error_message="error",
        )
        self.assertOptimizesTo(
            [
                migrations.AddConstraint("Pony", constraint),
                migrations.AlterConstraint("Pony", "pink_gt_2", constraint_with_error),
            ],
            [migrations.AddConstraint("Pony", constraint_with_error)],
        )