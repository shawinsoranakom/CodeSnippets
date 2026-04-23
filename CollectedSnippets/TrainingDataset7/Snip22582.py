def test_floatfield_step_size_min_value(self):
        f = FloatField(step_size=0.02, min_value=0.01)
        msg = (
            "Ensure this value is a multiple of step size 0.02, starting from 0.01, "
            "e.g. 0.01, 0.03, 0.05, and so on."
        )
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("0.02")
        self.assertEqual(f.clean("2.33"), 2.33)
        self.assertEqual(f.clean("0.11"), 0.11)
        self.assertEqual(f.step_size, 0.02)