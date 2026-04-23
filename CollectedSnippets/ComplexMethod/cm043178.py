def fast_format_html(html_string):
    """
    A fast HTML formatter that uses string operations instead of parsing.

    Args:
        html_string (str): The HTML string to format

    Returns:
        str: The formatted HTML string
    """
    # Initialize variables
    indent = 0
    indent_str = "  "  # Two spaces for indentation
    formatted = []
    # in_content = False

    # Split by < and > to separate tags and content
    parts = html_string.replace(">", ">\n").replace("<", "\n<").split("\n")

    for part in parts:
        if not part.strip():
            continue

        # Handle closing tags
        if part.startswith("</"):
            indent -= 1
            formatted.append(indent_str * indent + part)

        # Handle self-closing tags
        elif part.startswith("<") and part.endswith("/>"):
            formatted.append(indent_str * indent + part)

        # Handle opening tags
        elif part.startswith("<"):
            formatted.append(indent_str * indent + part)
            indent += 1

        # Handle content between tags
        else:
            content = part.strip()
            if content:
                formatted.append(indent_str * indent + content)

    return "\n".join(formatted)