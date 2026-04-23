def test_autoescape(self):
        self.assertEqual(
            join(["<a>", "<img>", "</a>"], "<br>"),
            "&lt;a&gt;&lt;br&gt;&lt;img&gt;&lt;br&gt;&lt;/a&gt;",
        )