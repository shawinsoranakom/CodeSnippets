def escape_format_html_block(context, content):
    """A block tag that uses format_html"""
    return format_html("Hello {0}: {1}!", context["name"], content)