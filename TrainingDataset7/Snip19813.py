def test_repr_with_violation_error_code(self):
        constraint = models.UniqueConstraint(
            models.F("baz__lower"),
            name="unique_lower_baz",
            violation_error_code="baz",
        )
        self.assertEqual(
            repr(constraint),
            (
                "<UniqueConstraint: expressions=(F(baz__lower),) "
                "name='unique_lower_baz' violation_error_code='baz'>"
            ),
        )