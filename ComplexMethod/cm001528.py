def resolve_var(name: str, gradio_theme=None, history=None):
    """
    Attempt to resolve a theme variable name to its value

    Parameters:
        name (str): The name of the theme variable
            ie "background_fill_primary", "background_fill_primary_dark"
            spaces and asterisk (*) prefix is removed from name before lookup
        gradio_theme (gradio.themes.ThemeClass): The theme object to resolve the variable from
            blank to use the webui default shared.gradio_theme
        history (list): A list of previously resolved variables to prevent circular references
            for regular use leave blank
    Returns:
        str: The resolved value

    Error handling:
        return either #000000 or #ffffff depending on initial name ending with "_dark"
    """
    try:
        if history is None:
            history = []
        if gradio_theme is None:
            gradio_theme = shared.gradio_theme

        name = name.strip()
        name = name[1:] if name.startswith("*") else name

        if name in history:
            raise ValueError(f'Circular references: name "{name}" in {history}')

        if value := getattr(gradio_theme, name, None):
            return resolve_var(value, gradio_theme, history + [name])
        else:
            return name

    except Exception:
        name = history[0] if history else name
        errors.report(f'resolve_color({name})', exc_info=True)
        return '#000000' if name.endswith("_dark") else '#ffffff'