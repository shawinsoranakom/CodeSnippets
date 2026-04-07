def test_nested3(self):
        self.assertEqual(
            unordered_list(["item 1", "item 2", ["item 2.1"]]),
            "\t<li>item 1</li>\n\t<li>item 2\n\t<ul>\n\t\t<li>item 2.1"
            "</li>\n\t</ul>\n\t</li>",
        )