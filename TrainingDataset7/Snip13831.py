def form_renderer_changed(*, setting, **kwargs):
    if setting == "FORM_RENDERER":
        from django.forms.renderers import get_default_renderer

        get_default_renderer.cache_clear()