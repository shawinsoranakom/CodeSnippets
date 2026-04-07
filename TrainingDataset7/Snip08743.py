def color_style(force_color=False):
    """
    Return a Style object from the Django color scheme.
    """
    if not force_color and not supports_color():
        return no_style()
    return make_style(os.environ.get("DJANGO_COLORS", ""))