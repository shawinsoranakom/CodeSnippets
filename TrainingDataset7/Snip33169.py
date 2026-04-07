def test_unordered_list05(self):
        output = self.engine.render_to_string("unordered_list05", {"a": ["x>", ["<y"]]})
        self.assertEqual(output, "\t<li>x>\n\t<ul>\n\t\t<li><y</li>\n\t</ul>\n\t</li>")