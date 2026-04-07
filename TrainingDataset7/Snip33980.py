def test_static_statictag02(self):
        output = self.engine.render_to_string(
            "static-statictag02", {"base_css": "admin/base.css"}
        )
        self.assertEqual(output, urljoin(settings.STATIC_URL, "admin/base.css"))