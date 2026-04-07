def test_nested2(self):
        self.assertEqual(
            unordered_list(["item 1", ["item 1.1", "item1.2"], "item 2"]),
            "\t<li>item 1\n\t<ul>\n\t\t<li>item 1.1</li>\n\t\t<li>item1.2"
            "</li>\n\t</ul>\n\t</li>\n\t<li>item 2</li>",
        )