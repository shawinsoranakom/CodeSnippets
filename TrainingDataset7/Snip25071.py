def test_pgettext(self):
        trans_real._active = Local()
        trans_real._translations = {}
        with translation.override("de"):
            self.assertEqual(pgettext("unexisting", "May"), "May")
            self.assertEqual(pgettext("month name", "May"), "Mai")
            self.assertEqual(pgettext("verb", "May"), "Kann")
            self.assertEqual(
                npgettext("search", "%d result", "%d results", 4) % 4, "4 Resultate"
            )