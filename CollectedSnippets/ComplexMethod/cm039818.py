def check_docstring_parameters(func, doc=None, ignore=None):
    """Helper to check docstring.

    Parameters
    ----------
    func : callable
        The function object to test.
    doc : str, default=None
        Docstring if it is passed manually to the test.
    ignore : list, default=None
        Parameters to ignore.

    Returns
    -------
    incorrect : list
        A list of string describing the incorrect results.
    """
    from numpydoc import docscrape

    incorrect = []
    ignore = [] if ignore is None else ignore

    func_name = _get_func_name(func)
    if not func_name.startswith("sklearn.") or func_name.startswith(
        "sklearn.externals"
    ):
        return incorrect
    # Don't check docstring for property-functions
    if inspect.isdatadescriptor(func):
        return incorrect
    # Don't check docstring for setup / teardown pytest functions
    if func_name.split(".")[-1] in ("setup_module", "teardown_module"):
        return incorrect
    # Dont check estimator_checks module
    if func_name.split(".")[2] == "estimator_checks":
        return incorrect
    # Get the arguments from the function signature
    param_signature = list(filter(lambda x: x not in ignore, _get_args(func)))
    # drop self
    if len(param_signature) > 0 and param_signature[0] == "self":
        param_signature.remove("self")

    # Analyze function's docstring
    if doc is None:
        records = []
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("error", UserWarning)
            try:
                doc = docscrape.FunctionDoc(func)
            except UserWarning as exp:
                if "potentially wrong underline length" in str(exp):
                    # Catch warning raised as of numpydoc 1.2 when
                    # the underline length for a section of a docstring
                    # is not consistent.
                    message = str(exp).split("\n")[:3]
                    incorrect += [f"In function: {func_name}"] + message
                    return incorrect
                records.append(str(exp))
            except Exception as exp:
                incorrect += [func_name + " parsing error: " + str(exp)]
                return incorrect
        if len(records):
            raise RuntimeError("Error for %s:\n%s" % (func_name, records[0]))

    param_docs = []
    for name, type_definition, param_doc in doc["Parameters"]:
        # Type hints are empty only if parameter name ended with :
        if not type_definition.strip():
            if ":" in name and name[: name.index(":")][-1:].strip():
                incorrect += [
                    func_name
                    + " There was no space between the param name and colon (%r)" % name
                ]
            elif name.rstrip().endswith(":"):
                incorrect += [
                    func_name
                    + " Parameter %r has an empty type spec. Remove the colon"
                    % (name.lstrip())
                ]

        # Create a list of parameters to compare with the parameters gotten
        # from the func signature
        if "*" not in name:
            param_docs.append(name.split(":")[0].strip("` "))

    # If one of the docstring's parameters had an error then return that
    # incorrect message
    if len(incorrect) > 0:
        return incorrect

    # Remove the parameters that should be ignored from list
    param_docs = list(filter(lambda x: x not in ignore, param_docs))

    # The following is derived from pytest, Copyright (c) 2004-2017 Holger
    # Krekel and others, Licensed under MIT License. See
    # https://github.com/pytest-dev/pytest

    message = []
    for i in range(min(len(param_docs), len(param_signature))):
        if param_signature[i] != param_docs[i]:
            message += [
                "There's a parameter name mismatch in function"
                " docstring w.r.t. function signature, at index %s"
                " diff: %r != %r" % (i, param_signature[i], param_docs[i])
            ]
            break
    if len(param_signature) > len(param_docs):
        message += [
            "Parameters in function docstring have less items w.r.t."
            " function signature, first missing item: %s"
            % param_signature[len(param_docs)]
        ]

    elif len(param_signature) < len(param_docs):
        message += [
            "Parameters in function docstring have more items w.r.t."
            " function signature, first extra item: %s"
            % param_docs[len(param_signature)]
        ]

    # If there wasn't any difference in the parameters themselves between
    # docstring and signature including having the same length then return
    # empty list
    if len(message) == 0:
        return []

    import difflib
    import pprint

    param_docs_formatted = pprint.pformat(param_docs).splitlines()
    param_signature_formatted = pprint.pformat(param_signature).splitlines()

    message += ["Full diff:"]

    message.extend(
        line.strip()
        for line in difflib.ndiff(param_signature_formatted, param_docs_formatted)
    )

    incorrect.extend(message)

    # Prepend function name
    incorrect = ["In function: " + func_name] + incorrect

    return incorrect