def test_unordered_list02(self):
        output = self.engine.render_to_string("unordered_list02", {"a": ["x>", ["<y"]]})
        self.assertEqual(output, "\t<li>x>\n\t<ul>\n\t\t<li><y</li>\n\t</ul>\n\t</li>")