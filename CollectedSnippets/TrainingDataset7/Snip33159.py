def test_truncate2(self):
        self.assertEqual(
            truncatewords_html(
                '<p>one <a href="#">two - three <br>four</a> five</p>', 4
            ),
            '<p>one <a href="#">two - three <br> …</a></p>',
        )