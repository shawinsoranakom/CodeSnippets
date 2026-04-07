def test_invalid_check_types(self):
        msg = "CheckConstraint.condition must be a Q instance or boolean expression."
        with self.assertRaisesMessage(TypeError, msg):
            models.CheckConstraint(condition=models.F("discounted_price"), name="check")