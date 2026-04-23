def test_cycle14(self):
        output = self.engine.render_to_string("cycle14", {"one": "1", "two": "2"})
        self.assertEqual(output, "12")