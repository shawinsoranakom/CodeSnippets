def compare_pipeline_args_to_hub_spec(pipeline_class, hub_spec):
    """
    Compares the docstring of a pipeline class to the fields of the matching Hub input signature class to ensure that
    they match. This guarantees that Transformers pipelines can be used in inference without needing to manually
    refactor or rename inputs.
    """
    ALLOWED_TRANSFORMERS_ONLY_ARGS = ["timeout"]

    docstring = inspect.getdoc(pipeline_class.__call__).strip()
    docstring_args = set(parse_args_from_docstring_by_indentation(docstring))
    hub_args = set(get_arg_names_from_hub_spec(hub_spec))

    # Special casing: We allow the name of this arg to differ
    hub_generate_args = [
        hub_arg for hub_arg in hub_args if hub_arg.startswith("generate") or hub_arg.startswith("generation")
    ]
    docstring_generate_args = [
        docstring_arg
        for docstring_arg in docstring_args
        if docstring_arg.startswith("generate") or docstring_arg.startswith("generation")
    ]
    if (
        len(hub_generate_args) == 1
        and len(docstring_generate_args) == 1
        and hub_generate_args != docstring_generate_args
    ):
        hub_args.remove(hub_generate_args[0])
        docstring_args.remove(docstring_generate_args[0])

    # Special casing 2: We permit some transformers-only arguments that don't affect pipeline output
    for arg in ALLOWED_TRANSFORMERS_ONLY_ARGS:
        if arg in docstring_args and arg not in hub_args:
            docstring_args.remove(arg)

    if hub_args != docstring_args:
        error = [f"{pipeline_class.__name__} differs from JS spec {hub_spec.__name__}"]
        matching_args = hub_args & docstring_args
        huggingface_hub_only = hub_args - docstring_args
        transformers_only = docstring_args - hub_args
        if matching_args:
            error.append(f"Matching args: {matching_args}")
        if huggingface_hub_only:
            error.append(f"Huggingface Hub only: {huggingface_hub_only}")
        if transformers_only:
            error.append(f"Transformers only: {transformers_only}")
        raise ValueError("\n".join(error))