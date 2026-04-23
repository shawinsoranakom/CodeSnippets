def test_validate_pk_field(self):
        constraint_with_pk = models.CheckConstraint(
            condition=~models.Q(pk=models.F("age")),
            name="pk_not_age_check",
        )
        constraint_with_pk.validate(ChildModel, ChildModel(pk=1, age=2))
        msg = f"Constraint “{constraint_with_pk.name}” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint_with_pk.validate(ChildModel, ChildModel(pk=1, age=1))
        with self.assertRaisesMessage(ValidationError, msg):
            constraint_with_pk.validate(ChildModel, ChildModel(id=1, age=1))
        constraint_with_pk.validate(ChildModel, ChildModel(pk=1, age=1), exclude={"pk"})