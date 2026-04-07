def test_multiple_locale_deactivate(self):
        with translation.override("de", deactivate=True):
            t = Template("{{ _('No') }}")
        with translation.override("nl"):
            self.assertEqual(t.render(Context({})), "Nee")