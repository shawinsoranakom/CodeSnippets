def test_time00_l10n(self):
        with translation.override("fr"):
            output = self.engine.render_to_string("time00_l10n", {"dt": time(16, 25)})
        self.assertEqual(output, "16:25")