def test_empty_list(self):
        output = self.engine.render_to_string("empty_list", {"a": []})
        self.assertEqual(output, "")