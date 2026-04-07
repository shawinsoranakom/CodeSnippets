def test_verbatim_tag03(self):
        output = self.engine.render_to_string("verbatim-tag03")
        self.assertEqual(output, "It's the {% verbatim %} tag")