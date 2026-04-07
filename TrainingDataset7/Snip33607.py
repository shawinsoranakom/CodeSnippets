def test_filter04(self):
        output = self.engine.render_to_string("filter04", {"remove": "spam"})
        self.assertEqual(output, "django")