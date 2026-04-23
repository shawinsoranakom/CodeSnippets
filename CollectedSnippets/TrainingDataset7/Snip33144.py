def test_truncate(self):
        self.assertEqual(
            truncatechars_html(
                '<p>one <a href="#">two - three <br>four</a> five</p>', 4
            ),
            "<p>one…</p>",
        )