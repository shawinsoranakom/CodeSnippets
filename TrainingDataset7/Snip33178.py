def test_autoescape_off(self):
        self.assertEqual(
            unordered_list(["<a>item 1</a>", "item 2"], autoescape=False),
            "\t<li><a>item 1</a></li>\n\t<li>item 2</li>",
        )