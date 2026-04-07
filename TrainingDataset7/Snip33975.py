def test_static_prefixtag02(self):
        output = self.engine.render_to_string("static-prefixtag02")
        self.assertEqual(output, settings.STATIC_URL)