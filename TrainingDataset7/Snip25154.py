def test_plural_non_django_language(self):
        self.assertEqual(get_language(), "xyz")
        self.assertEqual(ngettext("year", "years", 2), "years")