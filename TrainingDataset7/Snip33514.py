def test_cycle25(self):
        output = self.engine.render_to_string("cycle25", {"a": "<"})
        self.assertEqual(output, "&lt;")