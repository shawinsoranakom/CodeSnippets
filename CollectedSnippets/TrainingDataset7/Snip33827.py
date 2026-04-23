def test_include_missing_template(self):
        """
        The correct template is identified as not existing
        when {% include %} specifies a template that does not exist.
        """
        engine = Engine(app_dirs=True, debug=True)
        template = engine.get_template("test_include_error.html")
        with self.assertRaisesMessage(TemplateDoesNotExist, "missing.html"):
            template.render(Context())