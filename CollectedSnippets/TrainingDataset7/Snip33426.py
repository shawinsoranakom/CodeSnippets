def test_basic_syntax21(self):
        output = self.engine.render_to_string("basic-syntax21")
        self.assertEqual(output, "a {{ moo %} b")