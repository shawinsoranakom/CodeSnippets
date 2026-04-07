def test_custom_violation_error_message(self):
        c = BaseConstraint(
            name="base_name", violation_error_message="custom %(name)s message"
        )
        self.assertEqual(c.get_violation_error_message(), "custom base_name message")