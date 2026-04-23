def test_check_constraint_array_contains(self):
        constraint = CheckConstraint(
            condition=Q(field__contains=[1]),
            name="array_contains",
        )
        msg = f"Constraint “{constraint.name}” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(IntegerArrayModel, IntegerArrayModel())
        constraint.validate(IntegerArrayModel, IntegerArrayModel(field=[1]))