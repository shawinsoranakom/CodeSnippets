def setUpClass(cls):
        cls.django_renderer = DjangoTemplates()
        cls.jinja2_renderer = Jinja2() if jinja2 else None
        cls.renderers = [cls.django_renderer] + (
            [cls.jinja2_renderer] if cls.jinja2_renderer else []
        )
        super().setUpClass()