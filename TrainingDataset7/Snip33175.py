def test_nested_multiple(self):
        self.assertEqual(
            unordered_list(["item 1", ["item 1.1", ["item 1.1.1", ["item 1.1.1.1"]]]]),
            "\t<li>item 1\n\t<ul>\n\t\t<li>item 1.1\n\t\t<ul>\n\t\t\t<li>"
            "item 1.1.1\n\t\t\t<ul>\n\t\t\t\t<li>item 1.1.1.1</li>\n\t\t\t"
            "</ul>\n\t\t\t</li>\n\t\t</ul>\n\t\t</li>\n\t</ul>\n\t</li>",
        )