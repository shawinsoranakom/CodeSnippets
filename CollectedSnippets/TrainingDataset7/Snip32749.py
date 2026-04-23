def test_render_requires_dict(self):
        """django.Template.render() requires a dict."""
        engine = DjangoTemplates(
            {
                "DIRS": [],
                "APP_DIRS": False,
                "NAME": "django",
                "OPTIONS": {},
            }
        )
        template = engine.from_string("")
        context = Context()
        request_context = RequestContext(self.request_factory.get("/"), {})
        msg = "context must be a dict rather than Context."
        with self.assertRaisesMessage(TypeError, msg):
            template.render(context)
        msg = "context must be a dict rather than RequestContext."
        with self.assertRaisesMessage(TypeError, msg):
            template.render(request_context)