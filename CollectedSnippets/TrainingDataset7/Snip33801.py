def test_include01(self):
        output = self.engine.render_to_string("include01")
        self.assertEqual(output, "something cool")