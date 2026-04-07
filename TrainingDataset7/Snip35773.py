def test_patterns_reported(self):
        # Regression for #17076
        with self.assertRaisesMessage(
            NoReverseMatch, r"1 pattern(s) tried: ['people/(?P<name>\\w+)/$']"
        ):
            # this url exists, but requires an argument
            reverse("people", args=[])