def tokenize(
    template: str, def_ldel: str = "{{", def_rdel: str = "}}"
) -> Iterator[tuple[str, str]]:
    """Tokenize a mustache template.

    Tokenizes a mustache template in a generator fashion, using file-like objects. It
    also accepts a string containing the template.

    Args:
        template: a file-like object, or a string of a mustache template
        def_ldel: The default left delimiter
            (`'{{'` by default, as in spec compliant mustache)
        def_rdel: The default right delimiter
            (`'}}'` by default, as in spec compliant mustache)

    Yields:
        Mustache tags in the form of a tuple `(tag_type, tag_key)` where `tag_type` is
            one of:

            * literal
            * section
            * inverted section
            * end
            * partial
            * no escape

            ...and `tag_key` is either the key or in the case of a literal tag, the
            literal itself.

    Raises:
        ChevronError: If there is a syntax error in the template.
    """
    global _CURRENT_LINE, _LAST_TAG_LINE
    _CURRENT_LINE = 1
    _LAST_TAG_LINE = None

    is_standalone = True
    open_sections = []
    l_del = def_ldel
    r_del = def_rdel

    while template:
        literal, template = grab_literal(template, l_del)

        # If the template is completed
        if not template:
            # Then yield the literal and leave
            yield ("literal", literal)
            break

        # Do the first check to see if we could be a standalone
        is_standalone = l_sa_check(template, literal, is_standalone)

        # Parse the tag
        tag, template = parse_tag(template, l_del, r_del)
        tag_type, tag_key = tag

        # Special tag logic

        # If we are a set delimiter tag
        if tag_type == "set delimiter":
            # Then get and set the delimiters
            dels = tag_key.strip().split(" ")
            l_del, r_del = dels[0], dels[-1]

        # If we are a section tag
        elif tag_type in {"section", "inverted section"}:
            # Then open a new section
            open_sections.append(tag_key)
            _LAST_TAG_LINE = _CURRENT_LINE

        # If we are an end tag
        elif tag_type == "end":
            # Then check to see if the last opened section
            # is the same as us
            try:
                last_section = open_sections.pop()
            except IndexError as e:
                msg = (
                    f'Trying to close tag "{tag_key}"\n'
                    "Looks like it was not opened.\n"
                    f"line {_CURRENT_LINE + 1}"
                )
                raise ChevronError(msg) from e
            if tag_key != last_section:
                # Otherwise we need to complain
                msg = (
                    f'Trying to close tag "{tag_key}"\n'
                    f'last open tag is "{last_section}"\n'
                    f"line {_CURRENT_LINE + 1}"
                )
                raise ChevronError(msg)

        # Do the second check to see if we're a standalone
        is_standalone = r_sa_check(template, tag_type, is_standalone)

        # Which if we are
        if is_standalone:
            # Remove the stuff before the newline
            template = template.split("\n", 1)[-1]

            # Partials need to keep the spaces on their left
            if tag_type != "partial":
                # But other tags don't
                literal = literal.rstrip(" ")

        # Start yielding
        # Ignore literals that are empty
        if literal:
            yield ("literal", literal)

        # Ignore comments and set delimiters
        if tag_type not in {"comment", "set delimiter?"}:
            yield (tag_type, tag_key)

    # If there are any open sections when we're done
    if open_sections:
        # Then we need to complain
        msg = (
            "Unexpected EOF\n"
            f'the tag "{open_sections[-1]}" was never closed\n'
            f"was opened at line {_LAST_TAG_LINE}"
        )
        raise ChevronError(msg)