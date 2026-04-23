def render(
    template: str | list[tuple[str, str]] = "",
    data: Mapping[str, Any] = EMPTY_DICT,
    partials_dict: Mapping[str, str] = EMPTY_DICT,
    padding: str = "",
    def_ldel: str = "{{",
    def_rdel: str = "}}",
    scopes: Scopes | None = None,
    warn: bool = False,  # noqa: FBT001,FBT002
    keep: bool = False,  # noqa: FBT001,FBT002
) -> str:
    """Render a mustache template.

    Renders a mustache template with a data scope and inline partial capability.

    Args:
        template: A file-like object or a string containing the template.
        data: A python dictionary with your data scope.
        partials_dict: A python dictionary which will be search for partials
            before the filesystem is.

            `{'include': 'foo'}` is the same as a file called include.mustache
            (defaults to `{}`).
        padding: This is for padding partials, and shouldn't be used
            (but can be if you really want to).
        def_ldel: The default left delimiter

            (`'{{'` by default, as in spec compliant mustache).
        def_rdel: The default right delimiter

            (`'}}'` by default, as in spec compliant mustache).
        scopes: The list of scopes that `get_key` will look through.
        warn: Log a warning when a template substitution isn't found in the data
        keep: Keep unreplaced tags when a substitution isn't found in the data.

    Returns:
        A string containing the rendered template.
    """
    # If the template is a sequence but not derived from a string
    if isinstance(template, Sequence) and not isinstance(template, str):
        # Then we don't need to tokenize it
        # But it does need to be a generator
        tokens: Iterator[tuple[str, str]] = (token for token in template)
    elif template in g_token_cache:
        tokens = (token for token in g_token_cache[template])
    else:
        # Otherwise make a generator
        tokens = tokenize(template, def_ldel, def_rdel)

    output = ""

    if scopes is None:
        scopes = [data]

    # Run through the tokens
    for tag, key in tokens:
        # Set the current scope
        current_scope = scopes[0]

        # If we're an end tag
        if tag == "end":
            # Pop out of the latest scope
            del scopes[0]

        # If the current scope is falsy and not the only scope
        elif not current_scope and len(scopes) != 1:
            if tag in {"section", "inverted section"}:
                # Set the most recent scope to a falsy value
                scopes.insert(0, False)

        # If we're a literal tag
        elif tag == "literal":
            # Add padding to the key and add it to the output
            output += key.replace("\n", "\n" + padding)

        # If we're a variable tag
        elif tag == "variable":
            # Add the html escaped key to the output
            thing = _get_key(
                key, scopes, warn=warn, keep=keep, def_ldel=def_ldel, def_rdel=def_rdel
            )
            if thing is True and key == ".":
                # if we've coerced into a boolean by accident
                # (inverted tags do this)
                # then get the un-coerced object (next in the stack)
                thing = scopes[1]
            if not isinstance(thing, str):
                thing = str(thing)
            output += _html_escape(thing)

        # If we're a no html escape tag
        elif tag == "no escape":
            # Just lookup the key and add it
            thing = _get_key(
                key, scopes, warn=warn, keep=keep, def_ldel=def_ldel, def_rdel=def_rdel
            )
            if not isinstance(thing, str):
                thing = str(thing)
            output += thing

        # If we're a section tag
        elif tag == "section":
            # Get the sections scope
            scope = _get_key(
                key, scopes, warn=warn, keep=keep, def_ldel=def_ldel, def_rdel=def_rdel
            )

            # If the scope is a callable (as described in
            # https://mustache.github.io/mustache.5.html)
            if callable(scope):
                # Generate template text from tags
                text = ""
                tags: list[tuple[str, str]] = []
                for token in tokens:
                    if token == ("end", key):
                        break

                    tags.append(token)
                    tag_type, tag_key = token
                    if tag_type == "literal":
                        text += tag_key
                    elif tag_type == "no escape":
                        text += f"{def_ldel}& {tag_key} {def_rdel}"
                    else:
                        text += "{}{} {}{}".format(
                            def_ldel,
                            {
                                "comment": "!",
                                "section": "#",
                                "inverted section": "^",
                                "end": "/",
                                "partial": ">",
                                "set delimiter": "=",
                                "no escape": "&",
                                "variable": "",
                            }[tag_type],
                            tag_key,
                            def_rdel,
                        )

                g_token_cache[text] = tags

                rend = scope(
                    text,
                    lambda template, data=None: render(
                        template,
                        data={},
                        partials_dict=partials_dict,
                        padding=padding,
                        def_ldel=def_ldel,
                        def_rdel=def_rdel,
                        scopes=(data and [data, *scopes]) or scopes,
                        warn=warn,
                        keep=keep,
                    ),
                )

                output += rend

            # If the scope is a sequence, an iterator or generator but not
            # derived from a string
            elif isinstance(scope, (Sequence, Iterator)) and not isinstance(scope, str):
                # Then we need to do some looping

                # Gather up all the tags inside the section
                # (And don't be tricked by nested end tags with the same key)
                # TODO: This feels like it still has edge cases, no?
                tags = []
                tags_with_same_key = 0
                for token in tokens:
                    if token == ("section", key):
                        tags_with_same_key += 1
                    if token == ("end", key):
                        tags_with_same_key -= 1
                        if tags_with_same_key < 0:
                            break
                    tags.append(token)

                # For every item in the scope
                for thing in scope:
                    # Append it as the most recent scope and render
                    new_scope = [thing, *scopes]
                    rend = render(
                        template=tags,
                        scopes=new_scope,
                        padding=padding,
                        partials_dict=partials_dict,
                        def_ldel=def_ldel,
                        def_rdel=def_rdel,
                        warn=warn,
                        keep=keep,
                    )

                    output += rend

            else:
                # Otherwise we're just a scope section
                scopes.insert(0, scope)

        # If we're an inverted section
        elif tag == "inverted section":
            # Add the flipped scope to the scopes
            scope = _get_key(
                key, scopes, warn=warn, keep=keep, def_ldel=def_ldel, def_rdel=def_rdel
            )
            scopes.insert(0, cast("Literal[False]", not scope))

        # If we're a partial
        elif tag == "partial":
            # Load the partial
            partial = _get_partial(key, partials_dict)

            # Find what to pad the partial with
            left = output.rpartition("\n")[2]
            part_padding = padding
            if left.isspace():
                part_padding += left

            # Render the partial
            part_out = render(
                template=partial,
                partials_dict=partials_dict,
                def_ldel=def_ldel,
                def_rdel=def_rdel,
                padding=part_padding,
                scopes=scopes,
                warn=warn,
                keep=keep,
            )

            # If the partial was indented
            if left.isspace():
                # then remove the spaces from the end
                part_out = part_out.rstrip(" \t")

            # Add the partials output to the output
            output += part_out

    return output