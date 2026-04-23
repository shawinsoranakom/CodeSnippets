def test_compile_tag_error_27956(self):
        """Errors in a child of {% extends %} are displayed correctly."""
        engine = self._engine(
            app_dirs=True,
            libraries={"tag_27584": "template_tests.templatetags.tag_27584"},
        )
        t = engine.get_template("27956_child.html")
        with self.assertRaises(TemplateSyntaxError) as e:
            t.render(Context())
        if self.debug_engine:
            self.assertEqual(e.exception.template_debug["during"], "{% badtag %}")