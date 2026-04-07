def test_multiple_locale_loadi18n_direct_switch(self):
        with translation.override("de"):
            t = Template("{% load i18n %}{{ _('No') }}")
        with translation.override("nl"):
            self.assertEqual(t.render(Context({})), "Nee")