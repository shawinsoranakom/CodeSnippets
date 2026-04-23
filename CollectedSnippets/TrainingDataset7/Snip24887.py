def test_prefixed_i18n_disabled(self):
        with translation.override("en"):
            self.assertEqual(reverse("prefixed"), "/prefixed/")
        with translation.override("nl"):
            self.assertEqual(reverse("prefixed"), "/prefixed/")