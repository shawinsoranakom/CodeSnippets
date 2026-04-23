def _get_io_specs(exported_program: torch.export.ExportedProgram) -> tuple[dict, dict]:
    """Get the input and output specs of the exported program."""

    nodes: dict[str, torch.fx.Node] = {
        node.name: node for node in exported_program.graph.nodes
    }
    user_inputs = [
        spec
        for spec in exported_program.graph_signature.input_specs
        if spec.kind == graph_signature.InputKind.USER_INPUT
    ]
    user_outputs = [
        spec
        for spec in exported_program.graph_signature.output_specs
        if spec.kind == graph_signature.OutputKind.USER_OUTPUT
    ]
    inputs: dict[str, torch._export.serde.schema.TensorMeta | str] = {}
    outputs: dict[str, torch._export.serde.schema.TensorMeta | str] = {}
    for spec in user_inputs:
        inputs = _log_spec_into_io_specs(spec, nodes, inputs)
    for spec in user_outputs:
        outputs = _log_spec_into_io_specs(spec, nodes, outputs)
    return inputs, outputs