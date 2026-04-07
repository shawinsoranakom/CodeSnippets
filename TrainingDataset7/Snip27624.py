def test_from_model_constraints(self):
        class ModelWithConstraints(models.Model):
            size = models.IntegerField()

            class Meta:
                constraints = [
                    models.CheckConstraint(
                        condition=models.Q(size__gt=1), name="size_gt_1"
                    )
                ]

        state = ModelState.from_model(ModelWithConstraints)
        model_constraints = ModelWithConstraints._meta.constraints
        state_constraints = state.options["constraints"]
        self.assertEqual(model_constraints, state_constraints)
        self.assertIsNot(model_constraints, state_constraints)
        self.assertIsNot(model_constraints[0], state_constraints[0])