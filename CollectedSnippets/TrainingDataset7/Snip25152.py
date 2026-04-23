def test_non_django_language(self):
        self.assertEqual(get_language(), "xxx")
        self.assertEqual(gettext("year"), "reay")