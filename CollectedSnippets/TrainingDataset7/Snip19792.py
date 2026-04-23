def test_validate_jsonfield_exact(self):
        data = {"release": "5.0.2", "version": "stable"}
        json_exact_constraint = models.CheckConstraint(
            condition=models.Q(data__version="stable"),
            name="only_stable_version",
        )
        json_exact_constraint.validate(JSONFieldModel, JSONFieldModel(data=data))

        data = {"release": "5.0.2", "version": "not stable"}
        msg = f"Constraint “{json_exact_constraint.name}” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            json_exact_constraint.validate(JSONFieldModel, JSONFieldModel(data=data))