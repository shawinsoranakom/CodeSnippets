def test_if_is_not_match(self):
        # For this to act as a regression test, it's important not to use
        # foo=True because True is (not None)
        output = self.engine.render_to_string("template", {"foo": False})
        self.assertEqual(output, "yes")