def test_url03(self):
        output = self.engine.render_to_string("url03")
        self.assertEqual(output, "/")