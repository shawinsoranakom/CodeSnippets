def reset_loaders():
    from django.forms.renderers import get_default_renderer

    for backend in engines.all():
        if not isinstance(backend, DjangoTemplates):
            continue
        for loader in backend.engine.template_loaders:
            loader.reset()

    backend = getattr(get_default_renderer(), "engine", None)
    if isinstance(backend, DjangoTemplates):
        for loader in backend.engine.template_loaders:
            loader.reset()