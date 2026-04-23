def test_basic_syntax22(self):
        output = self.engine.render_to_string("basic-syntax22")
        self.assertEqual(output, "{{ moo #}")