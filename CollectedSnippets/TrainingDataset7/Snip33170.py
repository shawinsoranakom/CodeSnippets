def test_list(self):
        self.assertEqual(
            unordered_list(["item 1", "item 2"]), "\t<li>item 1</li>\n\t<li>item 2</li>"
        )