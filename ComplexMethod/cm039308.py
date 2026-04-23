def test_docstring_parameters():
    # Test module docstring formatting

    # Skip test if numpydoc is not found
    pytest.importorskip(
        "numpydoc", reason="numpydoc is required to test the docstrings"
    )

    # XXX unreached code as of v0.22
    from numpydoc import docscrape

    incorrect = []
    for name in PUBLIC_MODULES:
        if name.endswith(".conftest"):
            # pytest tooling, not part of the scikit-learn API
            continue
        if name == "sklearn.utils.fixes":
            # We cannot always control these docstrings
            continue
        with warnings.catch_warnings(record=True):
            module = importlib.import_module(name)
        classes = inspect.getmembers(module, inspect.isclass)
        # Exclude non-scikit-learn classes
        classes = [cls for cls in classes if cls[1].__module__.startswith("sklearn")]
        for cname, cls in classes:
            this_incorrect = []
            if cname in _DOCSTRING_IGNORES or cname.startswith("_"):
                continue
            if inspect.isabstract(cls):
                continue
            with warnings.catch_warnings(record=True) as w:
                cdoc = docscrape.ClassDoc(cls)
            if len(w):
                raise RuntimeError(
                    "Error for __init__ of %s in %s:\n%s" % (cls, name, w[0])
                )

            # Skip checks on deprecated classes
            if _is_deprecated(cls.__new__):
                continue

            this_incorrect += check_docstring_parameters(cls.__init__, cdoc)

            for method_name in cdoc.methods:
                method = getattr(cls, method_name)
                if _is_deprecated(method):
                    continue
                param_ignore = None
                # Now skip docstring test for y when y is None
                # by default for API reason
                if method_name in _METHODS_IGNORE_NONE_Y:
                    sig = signature(method)
                    if "y" in sig.parameters and sig.parameters["y"].default is None:
                        param_ignore = ["y"]  # ignore y for fit and score
                result = check_docstring_parameters(method, ignore=param_ignore)
                this_incorrect += result

            incorrect += this_incorrect

        functions = inspect.getmembers(module, inspect.isfunction)
        # Exclude imported functions
        functions = [fn for fn in functions if fn[1].__module__ == name]
        for fname, func in functions:
            # Don't test private methods / functions
            if fname.startswith("_"):
                continue
            if fname == "configuration" and name.endswith("setup"):
                continue
            name_ = _get_func_name(func)
            if not any(d in name_ for d in _DOCSTRING_IGNORES) and not _is_deprecated(
                func
            ):
                incorrect += check_docstring_parameters(func)

    msg = "\n".join(incorrect)
    if len(incorrect) > 0:
        raise AssertionError("Docstring Error:\n" + msg)