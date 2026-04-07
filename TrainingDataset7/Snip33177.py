def test_autoescape(self):
        self.assertEqual(
            unordered_list(["<a>item 1</a>", "item 2"]),
            "\t<li>&lt;a&gt;item 1&lt;/a&gt;</li>\n\t<li>item 2</li>",
        )