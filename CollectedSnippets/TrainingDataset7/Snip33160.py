def test_truncate3(self):
        self.assertEqual(
            truncatewords_html(
                '<p>one <a href="#">two - three <br>four</a> five</p>', 5
            ),
            '<p>one <a href="#">two - three <br>four</a> …</p>',
        )