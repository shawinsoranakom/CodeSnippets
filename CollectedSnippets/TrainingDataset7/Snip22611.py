def test_integerfield_step_size_min_value(self):
        f = IntegerField(step_size=3, min_value=-1)
        self.assertWidgetRendersTo(
            f,
            '<input name="f" min="-1" step="3" type="number" id="id_f" required>',
        )
        msg = (
            "Ensure this value is a multiple of step size 3, starting from -1, e.g. "
            "-1, 2, 5, and so on."
        )
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("9")
        self.assertEqual(f.clean("2"), 2)
        self.assertEqual(f.clean("-1"), -1)
        self.assertEqual(f.step_size, 3)