def test_template_mixin_without_template(self):
        """
        We want to makes sure that if you use a template mixin, but forget the
        template, it still tells you it's ImproperlyConfigured instead of
        TemplateDoesNotExist.
        """
        view = views.TemplateResponseWithoutTemplate()
        msg = (
            "SingleObjectTemplateResponseMixin requires a definition "
            "of 'template_name', 'template_name_field', or 'model'; "
            "or an implementation of 'get_template_names()'."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            view.get_template_names()