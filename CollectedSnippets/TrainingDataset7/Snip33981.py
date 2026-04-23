def test_static_statictag03(self):
        output = self.engine.render_to_string("static-statictag03")
        self.assertEqual(output, urljoin(settings.STATIC_URL, "admin/base.css"))