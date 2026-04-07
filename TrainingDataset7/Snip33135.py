def test_title2(self):
        output = self.engine.render_to_string("title2", {"a": "555 WEST 53RD STREET"})
        self.assertEqual(output, "555 West 53rd Street")