def test_multiple_locale_deactivate_trans(self):
        with translation.override("de", deactivate=True):
            t = self.get_template("{% load i18n %}{% translate 'No' %}")
        with translation.override("nl"):
            self.assertEqual(t.render(Context({})), "Nee")