def _convert_to_export_graph_signature(
    graph_signature: "GraphSignature",
    gm: "torch.fx.GraphModule",
    non_persistent_buffers: set[str],
) -> "ExportGraphSignature":
    from torch.utils import _pytree as pytree

    is_joint = graph_signature.backward_signature is not None

    # unpack objects
    user_inputs = set(graph_signature.user_inputs)
    inputs_to_parameters = graph_signature.inputs_to_parameters
    inputs_to_buffers = graph_signature.inputs_to_buffers
    user_outputs = set(graph_signature.user_outputs)
    buffer_mutations = graph_signature.buffers_to_mutate
    parameter_mutations = graph_signature.parameters_to_mutate
    user_input_mutations = graph_signature.user_inputs_to_mutate
    grad_params = (
        graph_signature.backward_signature.gradients_to_parameter  # type: ignore[union-attr]
        if is_joint
        else {}
    )
    grad_user_inputs = (
        graph_signature.backward_signature.gradients_to_user_inputs  # type: ignore[union-attr]
        if is_joint
        else {}
    )
    loss_output = (
        graph_signature.backward_signature.loss_output  # type: ignore[union-attr]
        if is_joint
        else None
    )
    input_tokens = graph_signature.input_tokens
    output_tokens = graph_signature.output_tokens

    inputs = [
        _make_argument_spec(node, input_tokens)
        for node in gm.graph.nodes
        if node.op == "placeholder"
    ]
    outputs = [
        _make_argument_spec(node, output_tokens)
        for node in pytree.tree_leaves(next(iter(reversed(gm.graph.nodes))).args)
    ]

    def to_input_spec(inp: ArgumentSpec) -> InputSpec:
        if isinstance(inp, TokenArgument):
            return InputSpec(kind=InputKind.TOKEN, arg=inp, target=None)

        if not isinstance(inp, TensorArgument):
            return InputSpec(kind=InputKind.USER_INPUT, arg=inp, target=None)
        name = inp.name
        if name in user_inputs:
            return InputSpec(kind=InputKind.USER_INPUT, arg=inp, target=None)
        elif name in inputs_to_parameters:
            return InputSpec(
                kind=InputKind.PARAMETER,
                arg=inp,
                target=inputs_to_parameters[name],  # type: ignore[index]
            )
        elif name in inputs_to_buffers:
            return InputSpec(
                kind=InputKind.BUFFER,
                arg=inp,
                target=inputs_to_buffers[name],  # type: ignore[index]
                persistent=(inputs_to_buffers[name] not in non_persistent_buffers),  # type: ignore[index]
            )
        else:
            raise AssertionError(f"Unknown tensor input kind: {name}")

    def to_output_spec(idx: int, o: ArgumentSpec) -> OutputSpec:
        if isinstance(o, TokenArgument):
            return OutputSpec(kind=OutputKind.TOKEN, arg=o, target=None)

        if not isinstance(o, TensorArgument):
            return OutputSpec(kind=OutputKind.USER_OUTPUT, arg=o, target=None)
        name = o.name
        if idx < len(buffer_mutations) + len(parameter_mutations) + len(
            user_input_mutations
        ) + len(output_tokens):
            if name in buffer_mutations:
                return OutputSpec(
                    kind=OutputKind.BUFFER_MUTATION,
                    arg=o,
                    target=buffer_mutations[name],  # type: ignore[index]
                )
            elif name in parameter_mutations:
                return OutputSpec(
                    kind=OutputKind.PARAMETER_MUTATION,
                    arg=o,
                    target=parameter_mutations[name],  # type: ignore[index]
                )
            elif name in user_input_mutations:
                return OutputSpec(
                    kind=OutputKind.USER_INPUT_MUTATION,
                    arg=o,
                    target=user_input_mutations[name],  # type: ignore[index]
                )
            else:
                raise AssertionError(f"Unknown tensor mutation kind: {name}")
        else:
            if name in user_outputs:
                return OutputSpec(kind=OutputKind.USER_OUTPUT, arg=o, target=None)

            elif name in grad_params:
                return OutputSpec(
                    kind=OutputKind.GRADIENT_TO_PARAMETER,
                    arg=o,
                    target=grad_params[name],
                )
            elif name in grad_user_inputs:
                return OutputSpec(
                    kind=OutputKind.GRADIENT_TO_USER_INPUT,
                    arg=o,
                    target=grad_user_inputs[name],
                )
            elif name == loss_output:
                return OutputSpec(kind=OutputKind.LOSS_OUTPUT, arg=o, target=None)

            else:
                raise AssertionError(f"Unknown tensor output kind: {name}")

    input_specs = [to_input_spec(inp) for inp in inputs]
    output_specs = [to_output_spec(idx, o) for idx, o in enumerate(outputs)]
    return ExportGraphSignature(input_specs=input_specs, output_specs=output_specs)