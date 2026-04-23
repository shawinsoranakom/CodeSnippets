def construct_relative_path(
    current_template_name,
    relative_name,
    allow_recursion=False,
):
    """
    Convert a relative path (starting with './' or '../') to the full template
    name based on the current_template_name.
    """
    new_name = relative_name.strip("'\"")
    if not new_name.startswith(("./", "../")):
        # relative_name is a variable or a literal that doesn't contain a
        # relative path.
        return relative_name

    if current_template_name is None:
        # Unknown origin (e.g. Template('...').render(Context({...})).
        raise TemplateSyntaxError(
            f"The relative path {relative_name} cannot be evaluated due to "
            "an unknown template origin."
        )

    new_name = posixpath.normpath(
        posixpath.join(
            posixpath.dirname(current_template_name.lstrip("/")),
            new_name,
        )
    )
    if new_name.startswith("../"):
        raise TemplateSyntaxError(
            "The relative path '%s' points outside the file hierarchy that "
            "template '%s' is in." % (relative_name, current_template_name)
        )
    if not allow_recursion and current_template_name.lstrip("/") == new_name:
        raise TemplateSyntaxError(
            "The relative path '%s' was translated to template name '%s', the "
            "same template in which the tag appears."
            % (relative_name, current_template_name)
        )
    has_quotes = (
        relative_name.startswith(('"', "'")) and relative_name[0] == relative_name[-1]
    )
    return f'"{new_name}"' if has_quotes else new_name