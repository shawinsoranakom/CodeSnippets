def test_no_prefix_translated(self):
        with translation.override("en"):
            self.assertEqual(reverse("no-prefix-translated"), "/translated/")
            self.assertEqual(
                reverse("no-prefix-translated-regex"), "/translated-regex/"
            )
            self.assertEqual(
                reverse("no-prefix-translated-slug", kwargs={"slug": "yeah"}),
                "/translated/yeah/",
            )

        with translation.override("nl"):
            self.assertEqual(reverse("no-prefix-translated"), "/vertaald/")
            self.assertEqual(reverse("no-prefix-translated-regex"), "/vertaald-regex/")
            self.assertEqual(
                reverse("no-prefix-translated-slug", kwargs={"slug": "yeah"}),
                "/vertaald/yeah/",
            )

        with translation.override("pt-br"):
            self.assertEqual(reverse("no-prefix-translated"), "/traduzidos/")
            self.assertEqual(
                reverse("no-prefix-translated-regex"), "/traduzidos-regex/"
            )
            self.assertEqual(
                reverse("no-prefix-translated-slug", kwargs={"slug": "yeah"}),
                "/traduzidos/yeah/",
            )