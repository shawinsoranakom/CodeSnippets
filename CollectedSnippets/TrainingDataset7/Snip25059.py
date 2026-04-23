def test_plural_null(self):
        g = trans_null.ngettext
        self.assertEqual(g("%(num)d year", "%(num)d years", 0) % {"num": 0}, "0 years")
        self.assertEqual(g("%(num)d year", "%(num)d years", 1) % {"num": 1}, "1 year")
        self.assertEqual(g("%(num)d year", "%(num)d years", 2) % {"num": 2}, "2 years")