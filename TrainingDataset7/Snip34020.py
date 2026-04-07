def test_url_fail02(self):
        with self.assertRaises(NoReverseMatch):
            self.engine.render_to_string("url-fail02")