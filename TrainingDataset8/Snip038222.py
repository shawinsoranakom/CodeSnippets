def clean_text(text: "SupportsStr") -> str:
    """Convert an object to text, dedent it, and strip whitespace."""
    return textwrap.dedent(str(text)).strip()