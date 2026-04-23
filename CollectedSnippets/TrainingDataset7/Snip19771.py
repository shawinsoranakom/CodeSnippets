def test_deconstruction(self):
        constraint = BaseConstraint(
            name="base_name",
            violation_error_message="custom %(name)s message",
            violation_error_code="custom_code",
        )
        path, args, kwargs = constraint.deconstruct()
        self.assertEqual(path, "django.db.models.BaseConstraint")
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs,
            {
                "name": "base_name",
                "violation_error_message": "custom %(name)s message",
                "violation_error_code": "custom_code",
            },
        )