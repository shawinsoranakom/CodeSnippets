def default_role_error(
    name, rawtext, text, lineno, inliner, options=None, content=None
):
    msg = (
        "Default role used (`single backticks`): %s. Did you mean to use two "
        "backticks for ``code``, or miss an underscore for a `link`_ ?" % rawtext
    )
    logger.warning(msg, location=(inliner.document.current_source, lineno))
    return [nodes.Text(text)], []