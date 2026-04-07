def test_get_generic_template(self):
        """
        Test a completely generic view that renders a template on GET
        with the template name as an argument at instantiation.
        """
        self._assert_about(
            TemplateView.as_view(template_name="generic_views/about.html")(
                self.rf.get("/about/")
            )
        )