def test_static_prefixtag03(self):
        output = self.engine.render_to_string("static-prefixtag03")
        self.assertEqual(output, settings.MEDIA_URL)