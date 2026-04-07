def test_nested(self):
        self.assertEqual(
            unordered_list(["item 1", ["item 1.1"]]),
            "\t<li>item 1\n\t<ul>\n\t\t<li>item 1.1</li>\n\t</ul>\n\t</li>",
        )