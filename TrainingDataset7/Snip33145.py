def test_truncate2(self):
        self.assertEqual(
            truncatechars_html(
                '<p>one <a href="#">two - three <br>four</a> five</p>', 9
            ),
            '<p>one <a href="#">two …</a></p>',
        )