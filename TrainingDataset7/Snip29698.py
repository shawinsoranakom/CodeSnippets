def test_check_constraint_array_length(self):
        constraint = CheckConstraint(
            condition=Q(field__len=1),
            name="array_length",
        )
        msg = f"Constraint “{constraint.name}” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(IntegerArrayModel, IntegerArrayModel())
        constraint.validate(IntegerArrayModel, IntegerArrayModel(field=[1]))