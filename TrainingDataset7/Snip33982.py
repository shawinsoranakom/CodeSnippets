def test_static_statictag04(self):
        output = self.engine.render_to_string(
            "static-statictag04", {"base_css": "admin/base.css"}
        )
        self.assertEqual(output, urljoin(settings.STATIC_URL, "admin/base.css"))