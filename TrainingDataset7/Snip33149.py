def test_invalid_arg(self):
        html = '<p>one <a href="#">two - three <br>four</a> five</p>'
        self.assertEqual(truncatechars_html(html, "a"), html)