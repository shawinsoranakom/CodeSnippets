def get_default():
        """
        Return the first DjangoTemplates backend that's configured, or raise
        ImproperlyConfigured if none are configured.

        This is required for preserving historical APIs that rely on a
        globally available, implicitly configured engine such as:

        >>> from django.template import Context, Template
        >>> template = Template("Hello {{ name }}!")
        >>> context = Context({'name': "world"})
        >>> template.render(context)
        'Hello world!'
        """
        # Since Engine is imported in django.template and since
        # DjangoTemplates is a wrapper around this Engine class,
        # local imports are required to avoid import loops.
        from django.template import engines
        from django.template.backends.django import DjangoTemplates

        for engine in engines.all():
            if isinstance(engine, DjangoTemplates):
                return engine.engine
        raise ImproperlyConfigured("No DjangoTemplates backend is configured.")