def test_static_statictag01(self):
        output = self.engine.render_to_string("static-statictag01")
        self.assertEqual(output, urljoin(settings.STATIC_URL, "admin/base.css"))