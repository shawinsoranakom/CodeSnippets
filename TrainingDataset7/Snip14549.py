def lazy_annotations():
    """
    inspect.getfullargspec eagerly evaluates type annotations. To add
    compatibility with Python 3.14+ deferred evaluation, patch the module-level
    helper to provide the annotation_format that we are using elsewhere.

    This private helper could be removed when there is an upstream solution for
    https://github.com/python/cpython/issues/141560.

    This context manager is not reentrant.
    """
    if not PY314:
        yield
        return
    with lock:
        original_helper = inspect._signature_from_callable
        inspect._signature_from_callable = safe_signature_from_callable
        try:
            yield
        finally:
            inspect._signature_from_callable = original_helper