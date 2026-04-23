def test_static_prefixtag01(self):
        output = self.engine.render_to_string("static-prefixtag01")
        self.assertEqual(output, settings.STATIC_URL)