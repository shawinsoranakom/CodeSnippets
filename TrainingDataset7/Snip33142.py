def test_truncatechars04(self):
        output = self.engine.render_to_string("truncatechars04", {"a": "abc"})
        self.assertEqual(output, "abc")