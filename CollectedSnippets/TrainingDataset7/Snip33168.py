def test_unordered_list04(self):
        output = self.engine.render_to_string(
            "unordered_list04", {"a": ["x>", [mark_safe("<y")]]}
        )
        self.assertEqual(output, "\t<li>x>\n\t<ul>\n\t\t<li><y</li>\n\t</ul>\n\t</li>")