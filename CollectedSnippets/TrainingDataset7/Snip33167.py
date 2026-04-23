def test_unordered_list03(self):
        output = self.engine.render_to_string(
            "unordered_list03", {"a": ["x>", [mark_safe("<y")]]}
        )
        self.assertEqual(
            output, "\t<li>x&gt;\n\t<ul>\n\t\t<li><y</li>\n\t</ul>\n\t</li>"
        )