def test_truncate(self):
        self.assertEqual(
            truncatewords_html(
                '<p>one <a href="#">two - three <br>four</a> five</p>', 2
            ),
            '<p>one <a href="#">two …</a></p>',
        )