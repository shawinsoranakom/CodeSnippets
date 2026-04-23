def test_invalid_order_by(self):
        msg = (
            "Window.order_by must be either a string reference to a field, an "
            "expression, or a list or tuple of them not {'-horse'}."
        )
        with self.assertRaisesMessage(ValueError, msg):
            Window(expression=Sum("power"), order_by={"-horse"})