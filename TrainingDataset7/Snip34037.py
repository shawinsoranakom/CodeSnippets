def test_url_asvar01(self):
        output = self.engine.render_to_string("url-asvar01")
        self.assertEqual(output, "")