def reset_template_engines(*, setting, **kwargs):
    if setting in {
        "TEMPLATES",
        "DEBUG",
        "INSTALLED_APPS",
    }:
        from django.template import engines

        try:
            del engines.templates
        except AttributeError:
            pass
        engines._templates = None
        engines._engines = {}
        from django.template.engine import Engine

        Engine.get_default.cache_clear()
        from django.forms.renderers import get_default_renderer

        get_default_renderer.cache_clear()