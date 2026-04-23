def test_length06(self):
        output = self.engine.render_to_string("length06", {"int": 7})
        self.assertEqual(output, "0")