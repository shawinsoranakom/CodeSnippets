def test_multiple_locale(self):
        with translation.override("de"):
            t = Template("{{ _('No') }}")
        with translation.override(self._old_language), translation.override("nl"):
            self.assertEqual(t.render(Context({})), "Nee")