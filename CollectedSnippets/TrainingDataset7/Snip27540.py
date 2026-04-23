def test_multiple_alter_constraints(self):
        gt_constraint_violation_msg_added = models.CheckConstraint(
            condition=models.Q(pink__gt=2),
            name="pink_gt_2",
            violation_error_message="ERROR",
        )
        gt_constraint_violation_msg_altered = models.CheckConstraint(
            condition=models.Q(pink__gt=2),
            name="pink_gt_2",
            violation_error_message="error",
        )
        self.assertOptimizesTo(
            [
                migrations.AlterConstraint(
                    "Pony", "pink_gt_2", gt_constraint_violation_msg_added
                ),
                migrations.AlterConstraint(
                    "Pony", "pink_gt_2", gt_constraint_violation_msg_altered
                ),
            ],
            [
                migrations.AlterConstraint(
                    "Pony", "pink_gt_2", gt_constraint_violation_msg_altered
                )
            ],
        )
        other_constraint_violation_msg = models.CheckConstraint(
            condition=models.Q(weight__gt=3),
            name="pink_gt_3",
            violation_error_message="error",
        )
        self.assertDoesNotOptimize(
            [
                migrations.AlterConstraint(
                    "Pony", "pink_gt_2", gt_constraint_violation_msg_added
                ),
                migrations.AlterConstraint(
                    "Pony", "pink_gt_3", other_constraint_violation_msg
                ),
            ]
        )