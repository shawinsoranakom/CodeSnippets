def get_type_hint_captures(fn):
    """
    Get a dictionary containing type resolution mappings necessary to resolve types
    for the literal annotations on 'fn'. These are not considered to be closed-over by fn
    and must be obtained separately (e.g. using this function).

    Args:
        fn: A callable.
    Returns:
        A Dict[str, Any] containing a mapping from the literal annotations used on
        fn to the Python objects they refer to.
    """
    # First, try to get the source of the function. We'll need to parse it to find the actual string names
    # that were used to annotate the types, since inspect.signature() will only return the class object that
    # the annotation refers to, not the string name. If we can't get the source, simply return an empty dict.
    # This may happen in cases where the function is synthesized dynamically at runtime.
    src = loader.get_source(fn)
    if src is None:
        try:
            src = inspect.getsource(fn)
        except OSError as e:
            raise OSError(
                f"Failed to get source for {fn} using inspect.getsource"
            ) from e

    # Gather a dictionary of parameter name -> type, skipping any parameters whose annotated
    # types are strings. These are only understood by TorchScript in the context of a type annotation
    # that refers to a class in its own definition, but trying to include a mapping for this in the result
    # function would cause infinite recursion because the class is currently being compiled.
    # In addition, there is logic in ScriptTypeParser to handle this.
    signature = inspect.signature(fn)
    name_to_type = {
        name: parameter.annotation
        for name, parameter in signature.parameters.items()
        if parameter.annotation is not inspect.Parameter.empty
        and not isinstance(parameter.annotation, str)
    }

    # Then, get the literal type annotations from the function declaration
    # by source inspection. This accounts for the case in which aliases are used
    # to annotate the arguments (e.g device_t = torch.device, and then d: device_t).
    # frontend.py cannot be used here because it includes _jit_internal, so use ast instead.
    a = ast.parse(textwrap.dedent(src))
    if len(a.body) != 1 or not isinstance(a.body[0], ast.FunctionDef):
        raise RuntimeError(f"Expected {fn} to be a function")
    f = a.body[0]

    # Prepare a dictionary of source annotation -> type, which will be the final result of this function,
    # by using the parsed AST (f) to reconstruct source annotations as strings for each parameter and mapping
    # them to the type object corresponding to the annotation via name_to_type using the parameter name.
    annotation_to_type = {}

    for arg in f.args.args:
        # Get the source type annotation string for this argument if possible.
        arg_annotation_str = (
            get_annotation_str(arg.annotation) if arg.annotation else None
        )

        # If the argument has no annotation or get_annotation_str cannot convert it to a string,
        # arg_annotation_str will be None. Skip this arg; ScriptTypeParser will probably handle
        # this in the latter case.
        if arg_annotation_str is None:
            continue

        # Insert {arg_annotation_str: type} into annotation_to_type if possible. One reason arg_name may not
        # be present in name_to_type is that the annotation itself is a string and not a type object
        # (common for self-refential annotations in classes). Once again, let ScriptTypeParser handle this.
        arg_name = arg.arg
        if arg_name in name_to_type:
            annotation_to_type[arg_annotation_str] = name_to_type[arg_name]

    # If there is a valid return annotation, include it in annotation_to_type. As with argument annotations,
    # the literal annotation has to be convertible to a string by get_annotation_str, and the actual type
    # of the annotation cannot be a string.
    literal_return_annotation = get_annotation_str(f.returns)
    valid_literal_annotation = literal_return_annotation is not None
    return_annotation = signature.return_annotation
    valid_return_annotation_type = (
        return_annotation is not inspect.Parameter.empty
        and not isinstance(return_annotation, str)
    )
    if valid_literal_annotation and valid_return_annotation_type:
        annotation_to_type[literal_return_annotation] = return_annotation

    return annotation_to_type