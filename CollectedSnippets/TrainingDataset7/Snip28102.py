def test_constraint_validation_key_transform(self):
        constraint = CheckConstraint(
            condition=Q(value__has_key="name") & ~Q(value__name=JSONNull()),
            name="check_value_name_not_json_null",
        )
        constraint.validate(
            NullableJSONModel, NullableJSONModel(value={"name": "Django"})
        )
        msg = f"Constraint “{constraint.name}” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(
                NullableJSONModel, NullableJSONModel(value={"name": None})
            )