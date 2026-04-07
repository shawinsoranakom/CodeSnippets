def test_extends_include_missing_baseloader(self):
        """
        #12787 -- The correct template is identified as not existing
        when {% extends %} specifies a template that does exist, but that
        template has an {% include %} of something that does not exist.
        """
        engine = Engine(app_dirs=True, debug=True)
        template = engine.get_template("test_extends_error.html")
        with self.assertRaisesMessage(TemplateDoesNotExist, "missing.html"):
            template.render(Context())