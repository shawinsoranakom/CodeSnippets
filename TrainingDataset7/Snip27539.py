def test_add_remove_constraint(self):
        gt_constraint = models.CheckConstraint(
            condition=models.Q(pink__gt=2), name="constraint_pony_pink_gt_2"
        )
        self.assertOptimizesTo(
            [
                migrations.AddConstraint("Pony", gt_constraint),
                migrations.RemoveConstraint("Pony", gt_constraint.name),
            ],
            [],
        )
        self.assertDoesNotOptimize(
            [
                migrations.AddConstraint("Pony", gt_constraint),
                migrations.RemoveConstraint("Pony", "other_name"),
            ],
        )