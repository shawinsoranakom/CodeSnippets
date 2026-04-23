def test_integerfield_6(self):
        f = IntegerField(step_size=3)
        self.assertWidgetRendersTo(
            f,
            '<input name="f" step="3" type="number" id="id_f" required>',
        )
        with self.assertRaisesMessage(
            ValidationError, "'Ensure this value is a multiple of step size 3.'"
        ):
            f.clean("10")
        self.assertEqual(12, f.clean(12))
        self.assertEqual(12, f.clean("12"))
        self.assertEqual(f.step_size, 3)