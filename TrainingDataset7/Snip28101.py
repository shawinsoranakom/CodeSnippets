def test_constraint_validation(self):
        constraint = CheckConstraint(
            condition=~Q(value=JSONNull()), name="check_not_json_null"
        )
        constraint.validate(NullableJSONModel, NullableJSONModel(value={"key": None}))
        msg = f"Constraint “{constraint.name}” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(NullableJSONModel, NullableJSONModel(value=JSONNull()))