def test_template_name_required(self):
        """
        A template view must provide a template name.
        """
        msg = (
            "TemplateResponseMixin requires either a definition of "
            "'template_name' or an implementation of 'get_template_names()'"
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.client.get("/template/no_template/")