def test_validate_nullable_jsonfield(self):
        is_null_constraint = models.CheckConstraint(
            condition=models.Q(data__isnull=True),
            name="nullable_data",
        )
        is_not_null_constraint = models.CheckConstraint(
            condition=models.Q(data__isnull=False),
            name="nullable_data",
        )
        is_null_constraint.validate(JSONFieldModel, JSONFieldModel(data=None))
        msg = f"Constraint “{is_null_constraint.name}” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            is_null_constraint.validate(JSONFieldModel, JSONFieldModel(data={}))
        msg = f"Constraint “{is_not_null_constraint.name}” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            is_not_null_constraint.validate(JSONFieldModel, JSONFieldModel(data=None))
        is_not_null_constraint.validate(JSONFieldModel, JSONFieldModel(data={}))