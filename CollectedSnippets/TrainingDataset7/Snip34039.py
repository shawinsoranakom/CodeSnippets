def test_url_asvar03(self):
        output = self.engine.render_to_string("url-asvar03")
        self.assertEqual(output, "")