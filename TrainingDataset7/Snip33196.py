def test_urlencode02(self):
        output = self.engine.render_to_string("urlencode02", {"urlbit": "escape/slash"})
        self.assertEqual(output, "/test/escape%2Fslash/")