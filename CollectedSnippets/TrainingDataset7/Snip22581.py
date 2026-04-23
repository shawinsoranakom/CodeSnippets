def test_floatfield_4(self):
        f = FloatField(step_size=0.02)
        self.assertWidgetRendersTo(
            f,
            '<input name="f" step="0.02" type="number" id="id_f" required>',
        )
        msg = "'Ensure this value is a multiple of step size 0.02.'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("0.01")
        self.assertEqual(2.34, f.clean("2.34"))
        self.assertEqual(2.1, f.clean("2.1"))
        self.assertEqual(-0.50, f.clean("-.5"))
        self.assertEqual(-1.26, f.clean("-1.26"))
        self.assertEqual(f.step_size, 0.02)