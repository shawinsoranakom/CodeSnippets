def test_not_prefixed(self):
        with translation.override("en"):
            self.assertEqual(reverse("not-prefixed"), "/not-prefixed/")
            self.assertEqual(
                reverse("not-prefixed-included-url"), "/not-prefixed-include/foo/"
            )
        with translation.override("nl"):
            self.assertEqual(reverse("not-prefixed"), "/not-prefixed/")
            self.assertEqual(
                reverse("not-prefixed-included-url"), "/not-prefixed-include/foo/"
            )