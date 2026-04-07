def fast_cache_clearing():
    """Workaround for performance issues in minidom document checks.

    Speeds up repeated DOM operations by skipping unnecessary full traversal
    of the DOM tree.
    """
    module_helper_was_lambda = False
    if original_fn := getattr(minidom, "_in_document", None):
        module_helper_was_lambda = original_fn.__name__ == "<lambda>"
        if not module_helper_was_lambda:
            minidom._in_document = lambda node: bool(node.ownerDocument)
    try:
        yield
    finally:
        if original_fn and not module_helper_was_lambda:
            minidom._in_document = original_fn