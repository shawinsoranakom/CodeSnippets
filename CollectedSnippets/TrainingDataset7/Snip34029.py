def test_url_fail12(self):
        with self.assertRaises(NoReverseMatch):
            self.engine.render_to_string("url-fail12", {"named_url": "no_such_view"})