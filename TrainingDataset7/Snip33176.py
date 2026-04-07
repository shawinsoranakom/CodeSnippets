def test_nested_multiple2(self):
        self.assertEqual(
            unordered_list(["States", ["Kansas", ["Lawrence", "Topeka"], "Illinois"]]),
            "\t<li>States\n\t<ul>\n\t\t<li>Kansas\n\t\t<ul>\n\t\t\t<li>"
            "Lawrence</li>\n\t\t\t<li>Topeka</li>\n\t\t</ul>\n\t\t</li>"
            "\n\t\t<li>Illinois</li>\n\t</ul>\n\t</li>",
        )