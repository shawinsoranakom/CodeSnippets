def test_cycle16(self):
        output = self.engine.render_to_string("cycle16", {"one": "A", "two": "2"})
        self.assertEqual(output, "a2")