def escape_format_html(context):
    """A tag that uses format_html"""
    return format_html("Hello {0}!", context["name"])