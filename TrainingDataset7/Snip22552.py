def test_emailfield_not_required(self):
        f = EmailField(required=False)
        self.assertEqual("", f.clean(""))
        self.assertEqual("", f.clean(None))
        self.assertEqual("person@example.com", f.clean("person@example.com"))
        self.assertEqual(
            "example@example.com", f.clean("      example@example.com  \t   \t ")
        )
        with self.assertRaisesMessage(
            ValidationError, "'Enter a valid email address.'"
        ):
            f.clean("foo")