def test_compile_tag_extra_data(self):
        """Custom tags can pass extra data back to template."""
        engine = self._engine(
            app_dirs=True,
            libraries={"custom": "template_tests.templatetags.custom"},
        )
        t = engine.from_string("{% load custom %}{% extra_data %}")
        self.assertEqual(t.extra_data["extra_data"], "CUSTOM_DATA")