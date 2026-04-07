def test_urlconf_cache(self):
        with self.assertRaises(NoReverseMatch):
            reverse("first")
        with self.assertRaises(NoReverseMatch):
            reverse("second")

        with override_settings(ROOT_URLCONF=FirstUrls):
            self.client.get(reverse("first"))
            with self.assertRaises(NoReverseMatch):
                reverse("second")

            with override_settings(ROOT_URLCONF=SecondUrls):
                with self.assertRaises(NoReverseMatch):
                    reverse("first")
                self.client.get(reverse("second"))

            self.client.get(reverse("first"))
            with self.assertRaises(NoReverseMatch):
                reverse("second")

        with self.assertRaises(NoReverseMatch):
            reverse("first")
        with self.assertRaises(NoReverseMatch):
            reverse("second")