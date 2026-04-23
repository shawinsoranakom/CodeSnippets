def _validate_dynamic_axes(dynamic_axes, model, input_names, output_names) -> None:
    """Ensures dynamic axes argument is follows the expected format."""
    if len(dynamic_axes) == 0:
        return

    if hasattr(model, "graph"):
        # Extracting set of valid input/output names that shall be used for dynamic_axes
        if (input_names is None) or len(input_names) == 0:
            input_names = [x.debugName() for x in model.graph.inputs()]
        if (output_names is None) or len(output_names) == 0:
            output_names = [y.debugName() for y in model.graph.outputs()]

    valid_names = set((input_names or []) + (output_names or []))

    # If dynamic axes are provided as a list rather than dictionary, they should
    # first get converted to a dictionary in expected format. If desired axes names
    # are not provided for dynamic axes, automatic names shall be generated for
    # provided dynamic axes of specified input/output
    for key, value in dynamic_axes.items():
        if key not in valid_names:
            warnings.warn(
                f"Provided key {key} for dynamic axes is not a valid input/output name",
                stacklevel=2,
            )
        if isinstance(value, list):
            warnings.warn(
                "No names were found for specified dynamic axes of provided input."
                f"Automatically generated names will be applied to each dynamic axes of input {key}",
                stacklevel=2,
            )

            value_dict = {}
            for i, x in enumerate(value):
                if not isinstance(x, int):
                    raise ValueError(
                        "The type of axis index is expected to be an integer"
                    )
                if x in value_dict:
                    warnings.warn(
                        f"Duplicate dynamic axis index {x} was provided for input {key}.",
                        stacklevel=2,
                    )
                else:
                    value_dict[x] = str(key) + "_dynamic_axes_" + str(i + 1)
            dynamic_axes[key] = value_dict