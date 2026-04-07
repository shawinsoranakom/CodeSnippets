def test_emailfield_min_max_length(self):
        f = EmailField(min_length=10, max_length=15)
        self.assertWidgetRendersTo(
            f,
            '<input id="id_f" type="email" name="f" maxlength="15" minlength="10" '
            "required>",
        )
        with self.assertRaisesMessage(
            ValidationError,
            "'Ensure this value has at least 10 characters (it has 9).'",
        ):
            f.clean("a@foo.com")
        self.assertEqual("alf@foo.com", f.clean("alf@foo.com"))
        with self.assertRaisesMessage(
            ValidationError,
            "'Ensure this value has at most 15 characters (it has 20).'",
        ):
            f.clean("alf123456788@foo.com")