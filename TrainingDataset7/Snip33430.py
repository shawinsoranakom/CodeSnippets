def test_basic_syntax25(self):
        output = self.engine.render_to_string("basic-syntax25")
        self.assertEqual(output, "fred")