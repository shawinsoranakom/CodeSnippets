def _construct_named_inputs_and_attrs(
    signature: ir.schemas.OpSignature,
    args: Sequence[AllowedArgType],
    kwargs: Mapping[str, AllowedArgType],
) -> tuple[dict[str, AllowedArgType], dict[str, ValidAttributeType]]:
    """Construct two mappings: name to inputs and named to attributes based on the signature and args/kwargs.

    This function uses the OpSignature to determine which argument in args and kwargs corresponds to
    which parameter in the signature. ONNX node inputs are stored in named_inputs, and attributes are
    stored in named_attrs. If an _optional input_ is not provided, it is filled with None.

    Args:
        signature: The OpSignature for the node.
        args: The positional arguments for the node.
        kwargs: The keyword arguments for the node.

    Returns:
        A tuple of two mappings: named_inputs and named_attrs.

    Raises:
        ValueError: If a required parameter is not provided.
    """
    # 1. Construct the (named_inputs, named_attrs) mapping based on (args, kwargs) and the signature.
    #   a. Loop over all parameters in the signature and args together
    #   b. Depending on param.is_input, Record named_inputs[param.name] = arg or named_attrs[param.name] = arg
    #   c. Handle kwargs as well
    #   d. Fill in None if the input is not provided
    named_inputs: dict[str, Any] = {}
    named_attrs: dict[str, Any] = {}
    reversed_args_stack = list(reversed(args))
    for param in signature.params:
        if isinstance(param, ir.schemas.Parameter):
            # Handle inputs
            if reversed_args_stack:
                # First exhaust the positional arguments
                if param.variadic:
                    # Handle variadic arguments
                    named_inputs[param.name] = tuple(args)
                    reversed_args_stack.clear()
                else:
                    named_inputs[param.name] = reversed_args_stack.pop()  # type: ignore[assignment]
            elif param.name in kwargs:
                named_inputs[param.name] = kwargs[param.name]  # type: ignore[assignment]
            elif param.required:
                raise ValueError(
                    f"Required parameter '{param.name}' is not provided. "
                    f"Signature: {signature}. Args: {args}. Kwargs: {kwargs}."
                )
            else:
                logger.debug(
                    "Optional parameter '%s' is not provided. Added as None. Signature: %s",
                    param.name,
                    signature,
                )
                named_inputs[param.name] = None  # type: ignore[assignment]
        else:
            # Handle attributes
            attribute: ValidAttributeType | ir.Attr
            if not isinstance(param, ir.schemas.AttributeParameter):
                raise AssertionError(f"Expected AttributeParameter, got {type(param)}")
            if reversed_args_stack:
                # First exhaust the positional arguments
                attribute = reversed_args_stack.pop()  # type: ignore[assignment]
            elif param.name in kwargs:
                attribute = kwargs[param.name]  # type: ignore[assignment]
            elif param.default is not None:
                attribute = param.default
            else:
                attribute = None

            if attribute is None:
                if param.required:
                    raise ValueError(
                        f"Required attribute '{param.name}' is not provided. "
                        f"Signature: {signature}. Args: {args}. Kwargs: {kwargs}."
                    )
                else:
                    logger.debug(
                        "Optional attribute '%s' is None. Dropped. Signature: %s",
                        param.name,
                        signature,
                    )
                    continue

            if isinstance(attribute, ir.Attr):
                # Turn the attribute from an default value into an actual parameter for the node
                attr_copied = copy.copy(attribute)
                # Make sure the name is the same as the parameter name and not the name of the default parameter
                attr_copied.name = param.name
                attribute = attr_copied

            if isinstance(attribute, int) and param.type == ir.AttributeType.FLOAT:
                # Convert the attribute to float if needed. This happens in PyTorch
                # where an attribute marked as float can be passed as an int.
                attribute = float(attribute)
            named_attrs[param.name] = attribute
    return named_inputs, named_attrs