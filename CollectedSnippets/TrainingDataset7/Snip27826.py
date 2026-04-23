def test_save_nan_invalid(self):
        msg = "“nan” value must be a decimal number."
        for value in [float("nan"), math.nan, "nan"]:
            with self.subTest(value), self.assertRaisesMessage(ValidationError, msg):
                BigD.objects.create(d=value)