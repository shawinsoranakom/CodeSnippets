def test_multiple_locale_direct_switch(self):
        with translation.override("de"):
            t = Template("{{ _('No') }}")
        with translation.override("nl"):
            self.assertEqual(t.render(Context({})), "Nee")