def test_get_template_attribute(self):
        """
        Test a view that renders a template on GET with the template name as
        an attribute on the class.
        """
        self._assert_about(AboutTemplateAttributeView.as_view()(self.rf.get("/about/")))