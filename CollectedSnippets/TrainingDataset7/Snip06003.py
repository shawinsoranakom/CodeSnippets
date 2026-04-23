def split_explicit_title(text):
    """
    Split role content into title and target, if given.

    From sphinx.util.nodes.split_explicit_title. See:
    https://github.com/sphinx-doc/sphinx/blob/230ccf2/sphinx/util/nodes.py#L389
    """
    match = explicit_title_re.match(text)
    if match:
        return True, match.group(1), match.group(2)
    return False, text, text