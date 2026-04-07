def render_value_in_context(value, context):
    """
    Convert any value to a string to become part of a rendered template. This
    means escaping, if required, and conversion to a string. If value is a
    string, it's expected to already be translated.
    """
    value = template_localtime(value, use_tz=context.use_tz)
    value = localize(value, use_l10n=context.use_l10n)
    if context.autoescape:
        if not issubclass(type(value), str):
            value = str(value)
        return conditional_escape(value)
    else:
        return str(value)