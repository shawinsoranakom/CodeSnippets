def test_repr_with_violation_error_message(self):
        constraint = models.CheckConstraint(
            condition=models.Q(price__lt=1),
            name="price_lt_one",
            violation_error_message="More than 1",
        )
        self.assertEqual(
            repr(constraint),
            "<CheckConstraint: condition=(AND: ('price__lt', 1)) name='price_lt_one' "
            "violation_error_message='More than 1'>",
        )