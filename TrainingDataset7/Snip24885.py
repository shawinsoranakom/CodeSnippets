def test_prefixed(self):
        with translation.override("en"):
            self.assertEqual(reverse("prefixed"), "/en/prefixed/")
        with translation.override("nl"):
            self.assertEqual(reverse("prefixed"), "/nl/prefixed/")
        with translation.override(None):
            self.assertEqual(
                reverse("prefixed"), "/%s/prefixed/" % settings.LANGUAGE_CODE
            )