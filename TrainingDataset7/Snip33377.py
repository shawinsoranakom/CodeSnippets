def test_multiple_locale_filter_direct_switch(self):
        with translation.override("de"):
            t = Template("{% load i18n %}{{ 0|yesno:_('yes,no,maybe') }}")
        with translation.override("nl"):
            self.assertEqual(t.render(Context({})), "nee")