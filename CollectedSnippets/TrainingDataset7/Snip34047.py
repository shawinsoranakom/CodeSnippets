def test_verbatim_tag02(self):
        output = self.engine.render_to_string("verbatim-tag02")
        self.assertEqual(output, "{% endif %}")