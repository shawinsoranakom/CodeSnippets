def test_emailfield_1(self):
        f = EmailField()
        self.assertEqual(f.max_length, 320)
        self.assertWidgetRendersTo(
            f, '<input type="email" name="f" id="id_f" maxlength="320" required>'
        )
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean("")
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(None)
        self.assertEqual("person@example.com", f.clean("person@example.com"))
        with self.assertRaisesMessage(
            ValidationError, "'Enter a valid email address.'"
        ):
            f.clean("foo")
        self.assertEqual(
            "local@domain.with.idn.xyz\xe4\xf6\xfc\xdfabc.part.com",
            f.clean("local@domain.with.idn.xyzäöüßabc.part.com"),
        )