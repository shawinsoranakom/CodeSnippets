def test_root_element_escaped_html(self):
        html = "&lt;br&gt;"
        parsed = parse_html(html)
        self.assertEqual(str(parsed), html)