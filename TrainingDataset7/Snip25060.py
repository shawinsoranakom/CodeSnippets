def test_multiple_plurals_per_language(self):
        """
        Normally, French has 2 plurals. As
        other/locale/fr/LC_MESSAGES/django.po has a different plural equation
        with 3 plurals, this tests if those plural are honored.
        """
        self.assertEqual(ngettext("%d singular", "%d plural", 0) % 0, "0 pluriel1")
        self.assertEqual(ngettext("%d singular", "%d plural", 1) % 1, "1 singulier")
        self.assertEqual(ngettext("%d singular", "%d plural", 2) % 2, "2 pluriel2")
        french = trans_real.catalog()
        # Internal _catalog can query subcatalogs (from different po files).
        self.assertEqual(french._catalog[("%d singular", 0)], "%d singulier")
        self.assertEqual(french._catalog[("%(num)d hour", 0)], "%(num)d heure")