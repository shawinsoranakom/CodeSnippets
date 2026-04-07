def test_list_gettext(self):
        self.assertEqual(
            unordered_list(["item 1", gettext_lazy("item 2")]),
            "\t<li>item 1</li>\n\t<li>item 2</li>",
        )