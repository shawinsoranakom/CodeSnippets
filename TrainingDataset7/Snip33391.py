def test_autoescape_tag04(self):
        output = self.engine.render_to_string("autoescape-tag04", {"first": "<a>"})
        self.assertEqual(output, "<a> &lt;a&gt;")