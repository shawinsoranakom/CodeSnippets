def test_url_asvar02(self):
        output = self.engine.render_to_string("url-asvar02")
        self.assertEqual(output, "/")