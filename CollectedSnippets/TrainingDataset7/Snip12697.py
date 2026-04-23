def get_default_renderer():
    renderer_class = import_string(settings.FORM_RENDERER)
    return renderer_class()