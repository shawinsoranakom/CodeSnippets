def test_multiple_locale_trans(self):
        with translation.override("de"):
            t = self.get_template("{% load i18n %}{% translate 'No' %}")
        with translation.override(self._old_language), translation.override("nl"):
            self.assertEqual(t.render(Context({})), "Nee")