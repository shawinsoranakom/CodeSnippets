def test_autoescape_off(self):
        self.assertEqual(
            join(["<a>", "<img>", "</a>"], "<br>", autoescape=False),
            "<a><br><img><br></a>",
        )