def test_static_prefixtag04(self):
        output = self.engine.render_to_string("static-prefixtag04")
        self.assertEqual(output, settings.MEDIA_URL)