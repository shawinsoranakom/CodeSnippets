def _convert_fx_arg_to_onnx_arg(
    arg,
    node_name_to_values: dict[str, ir.Value | Sequence[ir.Value]],
    node_name_to_local_functions: dict[str, ir.Function],
) -> Any:
    """Convert an FX argument to an ONNX compatible argument.

    This function
    - Converts a torch dtype to an integer
    - Converts a torch device/memory_format/layout to a string
    - Converts a torch.fx.Node to an ir.Value
    - Converts a sequence of torch.fx.Node to a sequence of ir.Value
    - Converts a get_attr node to an ir.Function
    """
    if arg is None:
        # None arguments are not modified because when the arg is an ONNX input
        # we need to preserve the None value; when the arg is an ONNX attribute,
        # we want to drop the value.
        # The actual dropping of a None attribute value is done by OpRecorder
        return None
    if hasattr(arg, "name"):
        if isinstance(arg, torch.fx.Node) and arg.target is operator.getitem:
            source = arg.all_input_nodes[0]
            source_outputs = node_name_to_values[source.name]
            if isinstance(source_outputs, Sequence):
                # If the node is getting an input from another node, get the actual value the node is retrieving
                return _handle_getitem_node(arg, node_name_to_values)
            else:
                # `source_outputs` is a sequence(tensor()) value and we need to
                # use SequenceAt to get the value. This is handled by torchlib
                pass
        if isinstance(arg, torch.fx.Node) and arg.op == "get_attr":
            return node_name_to_local_functions[arg.name]
        # If the input is a node, get the value from the mapping
        return node_name_to_values[arg.name]
    if isinstance(arg, (list, tuple)):
        return [
            _convert_fx_arg_to_onnx_arg(
                elem, node_name_to_values, node_name_to_local_functions
            )
            for elem in arg
        ]
    if isinstance(arg, (torch.device, torch.memory_format, torch.layout)):
        return str(arg)
    if isinstance(arg, torch.dtype):
        return torch_dtype_to_onnx_dtype(arg)
    # Maybe a Python value
    return arg