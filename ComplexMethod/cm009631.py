def parse_tag(template: str, l_del: str, r_del: str) -> tuple[tuple[str, str], str]:
    """Parse a tag from a template.

    Args:
        template: The template.
        l_del: The left delimiter.
        r_del: The right delimiter.

    Returns:
        The tag and the template.

    Raises:
        ChevronError: If the tag is unclosed.
        ChevronError: If the set delimiter tag is unclosed.
    """
    tag_types = {
        "!": "comment",
        "#": "section",
        "^": "inverted section",
        "/": "end",
        ">": "partial",
        "=": "set delimiter?",
        "{": "no escape?",
        "&": "no escape",
    }

    # Get the tag
    try:
        tag, template = template.split(r_del, 1)
    except ValueError as e:
        msg = f"unclosed tag at line {_CURRENT_LINE}"
        raise ChevronError(msg) from e

    # Check for empty tags
    if not tag.strip():
        msg = f"empty tag at line {_CURRENT_LINE}"
        raise ChevronError(msg)

    # Find the type meaning of the first character
    tag_type = tag_types.get(tag[0], "variable")

    # If the type is not a variable
    if tag_type != "variable":
        # Then that first character is not needed
        tag = tag[1:]

    # If we might be a set delimiter tag
    if tag_type == "set delimiter?":
        # Double check to make sure we are
        if tag.endswith("="):
            tag_type = "set delimiter"
            # Remove the equal sign
            tag = tag[:-1]

        # Otherwise we should complain
        else:
            msg = f"unclosed set delimiter tag\nat line {_CURRENT_LINE}"
            raise ChevronError(msg)

    elif (
        # If we might be a no html escape tag
        tag_type == "no escape?"
        # And we have a third curly brace
        # (And are using curly braces as delimiters)
        and l_del == "{{"
        and r_del == "}}"
        and template.startswith("}")
    ):
        # Then we are a no html escape tag
        template = template[1:]
        tag_type = "no escape"

    # Strip the whitespace off the key and return
    return ((tag_type, tag.strip()), template)