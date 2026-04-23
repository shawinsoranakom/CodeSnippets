def _get_inputs_and_attributes(
    node: torch.fx.Node,
) -> tuple[list[torch.fx.Node | None], dict[str, Any], list[str], list[str]]:
    """Find and Fill in the not provided kwargs with default values.

    Returns:
        (inputs, attributes, input_names, output_names)
    """
    if inspect.isbuiltin(node.target) or isinstance(node.target, str):
        inputs = list(node.args)
        return inputs, {}, [], [node.name]  # type: ignore[return-value]

    # The target should be an ATen operator now
    if not hasattr(node.target, "_schema"):
        raise AssertionError(
            f"The target should be an ATen operator now, but node target {node.target} has no schema"
        )
    node_schema: torch.FunctionSchema = node.target._schema

    # This function assumes the order of arguments in FX op is the
    # same as the order of arguments in TorchScript op.
    inputs: list[Any] = []  # type: ignore[no-redef]
    input_names: list[str] = []
    attributes: dict[str, Any] = {}

    if inspect.isbuiltin(node.target):
        inputs = list(node.args)
    else:
        for arg, schema_arg in zip(node.args, node_schema.arguments):
            if arg is None or isinstance(arg, torch.fx.Node):
                inputs.append(arg)
                input_names.append(schema_arg.name)
            elif isinstance(arg, Sequence) and all(
                elem is None or isinstance(elem, torch.fx.Node) for elem in arg
            ):
                inputs.extend(arg)
                input_names.extend([schema_arg.name] * len(arg))
            elif isinstance(arg, torch.device):
                attributes[schema_arg.name] = str(arg)
            elif isinstance(arg, torch.dtype):
                attributes[schema_arg.name] = torch_dtype_to_onnx_dtype(arg)
            else:
                attributes[schema_arg.name] = arg
        for schema_arg in node_schema.arguments:
            if schema_arg.name not in node.kwargs:
                continue
            kwarg = node.kwargs[schema_arg.name]
            if schema_arg.name in {
                "layout",
                "device",
                "requires_grad",
                "memory_format",
                "implicit",
            } or isinstance(kwarg, torch.device):
                attr = str(kwarg)
            elif isinstance(kwarg, torch.dtype):
                attr = torch_dtype_to_onnx_dtype(kwarg)  # type: ignore[assignment]
            else:
                attr = kwarg  # type: ignore[assignment]

            attributes[schema_arg.name] = attr

    output_names = [f"{node.name}_{output.name}" for output in node_schema.returns]

    return inputs, attributes, input_names, output_names