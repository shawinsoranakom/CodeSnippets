def filter_errors(errors, method, Klass=None):
    """
    Ignore some errors based on the method type.

    These rules are specific for scikit-learn."""
    for code, message in errors:
        # We ignore following error code,
        #  - RT02: The first line of the Returns section
        #    should contain only the type, ..
        #   (as we may need to refer to the name of the returned
        #    object)
        #  - GL01: Docstring text (summary) should start in the line
        #    immediately after the opening quotes (not in the same line,
        #    or leaving a blank line in between)
        #  - GL02: If there's a blank line, it should be before the
        #    first line of the Returns section, not after (it allows to have
        #    short docstrings for properties).

        if code in ["RT02", "GL01", "GL02"]:
            continue

        # Ignore PR02: Unknown parameters for properties. We sometimes use
        # properties for ducktyping, i.e. SGDClassifier.predict_proba
        # Ignore GL08: Parsing of the method signature failed, possibly because this is
        # a property. Properties are sometimes used for deprecated attributes and the
        # attribute is already documented in the class docstring.
        #
        # All error codes:
        # https://numpydoc.readthedocs.io/en/latest/validation.html#built-in-validation-checks
        if code in ("PR02", "GL08") and Klass is not None and method is not None:
            method_obj = getattr(Klass, method)
            if isinstance(method_obj, property):
                continue

        # Following codes are only taken into account for the
        # top level class docstrings:
        #  - ES01: No extended summary found
        #  - SA01: See Also section not found
        #  - EX01: No examples section found

        if method is not None and code in ["EX01", "SA01", "ES01"]:
            continue
        yield code, message