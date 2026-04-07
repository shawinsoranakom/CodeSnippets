def test_ulitem_autoescape_off(self):
        class ULItem:
            def __init__(self, title):
                self.title = title

            def __str__(self):
                return "ulitem-%s" % str(self.title)

        a = ULItem("a")
        b = ULItem("b")
        c = ULItem("<a>c</a>")
        self.assertEqual(
            unordered_list([a, b, c], autoescape=False),
            "\t<li>ulitem-a</li>\n\t<li>ulitem-b</li>\n\t<li>ulitem-<a>c</a></li>",
        )

        def item_generator():
            yield from (a, b, c)

        self.assertEqual(
            unordered_list(item_generator(), autoescape=False),
            "\t<li>ulitem-a</li>\n\t<li>ulitem-b</li>\n\t<li>ulitem-<a>c</a></li>",
        )