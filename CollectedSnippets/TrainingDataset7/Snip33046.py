def test_empty_list(self):
        output = self.engine.render_to_string("empty_list", {"list": []})
        self.assertEqual(output, "")