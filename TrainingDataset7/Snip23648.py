def test_template_engine(self):
        """
        A template view may provide a template engine.
        """
        request = self.rf.get("/using/")
        view = TemplateView.as_view(template_name="generic_views/using.html")
        self.assertEqual(view(request).render().content, b"DTL\n")
        view = TemplateView.as_view(
            template_name="generic_views/using.html", template_engine="django"
        )
        self.assertEqual(view(request).render().content, b"DTL\n")
        view = TemplateView.as_view(
            template_name="generic_views/using.html", template_engine="jinja2"
        )
        self.assertEqual(view(request).render().content, b"Jinja2\n")