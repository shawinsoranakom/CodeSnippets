def canonicalize(
    ep: ExportedProgram, constants: set[str] | None = None
) -> ExportedProgram:
    """
    Normalize a serialized ExportedProgram, so that different eager program which
    shares the same semantics can get a single representation on disk.

    This function canonicalizes an ExportedProgram by:

    1. Sorting nodes in topological order.
    2. Rename nodes to have unique names.
    3. Remove unstable fields.
    4. Aggregate the above program fields.
    5. Recurse in subgraphs.

    Args:
        ep (ExportedProgram): The ExportedProgram to canonicalize.
        constants (Optional[set[str]]): Set of constants names

    Returns:
        ExportedProgram: The canonicalized exported program.
    """
    ep = copy.deepcopy(ep)
    # pyrefly: ignore [annotation-mismatch, redefinition]
    constants: set[str] = constants or set()

    opset_version = dict(sorted(ep.opset_version.items(), key=operator.itemgetter(0)))
    range_constraints = dict(
        sorted(ep.range_constraints.items(), key=operator.itemgetter(0))
    )
    guards_code = sorted(ep.guards_code)
    module_call_graph = sorted(ep.graph_module.module_call_graph, key=lambda x: x.fqn)
    signature = ep.graph_module.signature
    graph = ep.graph_module.graph

    if len(graph.inputs) != len(signature.input_specs):
        raise AssertionError(
            f"graph.inputs length {len(graph.inputs)} != signature.input_specs length {len(signature.input_specs)}"
        )
    if len(graph.outputs) != len(signature.output_specs):
        raise AssertionError(
            f"graph.outputs length {len(graph.outputs)} != signature.output_specs length {len(signature.output_specs)}"
        )

    def rank_input(inp) -> tuple[int, str | None, int]:
        idx, (_arg, spec) = inp
        if not isinstance(spec, InputSpec):
            raise AssertionError(f"expected InputSpec, got {type(spec).__name__}")
        if spec.type == "user_input":
            return 5, None, idx
        elif spec.type == "parameter":
            return 1, spec.parameter.parameter_name, idx
        elif spec.type == "buffer":
            return 2, spec.buffer.buffer_name, idx
        elif spec.type == "tensor_constant":
            return 3, spec.tensor_constant.tensor_constant_name, idx
        elif spec.type == "custom_obj":
            return 4, spec.custom_obj.custom_obj_name, idx
        elif spec.type == "token":
            return 0, None, idx
        elif spec.type == "constant_input":
            return 6, spec.constant_input.name, idx
        else:
            raise AssertionError(f"Unknown input type: {spec}")

    def rank_output(out) -> tuple[int, str | None, int]:
        idx, (_arg, spec) = out
        if not isinstance(spec, OutputSpec):
            raise AssertionError(f"expected OutputSpec, got {type(spec).__name__}")
        if spec.type == "user_output":
            return 4, None, idx
        elif spec.type == "loss_output":
            return 4, None, idx
        elif spec.type == "parameter_mutation":
            return 1, spec.parameter_mutation.parameter_name, idx
        elif spec.type == "buffer_mutation":
            return 2, spec.buffer_mutation.buffer_name, idx
        elif spec.type == "gradient_to_parameter":
            return 5, spec.gradient_to_parameter.parameter_name, idx
        elif spec.type == "gradient_to_user_input":
            return 6, None, idx
        elif spec.type == "user_input_mutation":
            return 3, None, idx
        elif spec.type == "token":
            return 0, None, idx
        else:
            raise AssertionError(f"Unknown output type: {spec}")

    sorted_ins = sorted(
        enumerate(zip(graph.inputs, signature.input_specs)), key=rank_input
    )

    if len(sorted_ins) > 0:
        sorted_inputs, input_specs = zip(*(i for idx, i in sorted_ins))  # type: ignore[assignment]
    else:
        sorted_inputs = ()
        input_specs = ()

    sorted_outs = sorted(
        enumerate(zip(graph.outputs, signature.output_specs)), key=rank_output
    )
    sorted_outputs, output_specs = zip(*(i for idx, i in sorted_outs))  # type: ignore[assignment]

    sorted_graph, replace_table = _canonicalize_graph(
        sorted_inputs, sorted_outputs, graph, constants
    )

    def replace_input(spec):
        if not isinstance(spec, InputSpec):
            raise AssertionError(f"expected InputSpec, got {type(spec).__name__}")
        if spec.type == "user_input":
            arg = spec.user_input.arg
            if arg.type == "as_tensor":
                t = arg.as_tensor
                t.name = replace_table[t.name]
            elif arg.type == "as_sym_int":
                s = arg.as_sym_int
                if s.type == "as_name":
                    s.as_name = replace_table[s.as_name]
                elif s.type == "as_int":
                    pass
                else:
                    raise AssertionError(f"Unknown sym_int type: {s}")
            elif arg.type == "as_sym_float":
                f = arg.as_sym_float
                if f.type == "as_name":
                    f.as_name = replace_table[f.as_name]
                elif f.type == "as_float":
                    pass
                else:
                    raise AssertionError(f"Unknown sym_float type: {f}")
            elif arg.type in (
                "as_none",
                "as_bool",
                "as_int",
                "as_float",
                "as_string",
                "as_custom_obj",
            ):
                return
            else:
                raise AssertionError(f"Unknown input type: {arg}")
        elif spec.type == "parameter":
            t = spec.parameter.arg
            t.name = replace_table[t.name]
        elif spec.type == "buffer":
            t = spec.buffer.arg
            t.name = replace_table[t.name]
        elif spec.type == "tensor_constant":
            t = spec.tensor_constant.arg
            t.name = replace_table[t.name]
        elif spec.type == "custom_obj":
            t_custom_obj = spec.custom_obj.arg
            t_custom_obj.name = replace_table[t_custom_obj.name]
            return
        elif spec.type == "token":
            tok = spec.token.arg
            tok.name = replace_table[tok.name]
        elif spec.type == "constant_input":
            return
        else:
            raise AssertionError(f"Unknown input type: {spec}")

    def replace_output(out):
        if not isinstance(spec, OutputSpec):
            raise AssertionError(f"expected OutputSpec, got {type(spec).__name__}")
        if spec.type == "user_output":
            arg = spec.user_output.arg
            if arg.type == "as_tensor":
                t = arg.as_tensor
                t.name = replace_table[t.name]
            elif arg.type == "as_sym_int":
                s = arg.as_sym_int
                if s.type == "as_name":
                    s.as_name = replace_table[s.as_name]
                elif s.type == "as_int":
                    pass
                else:
                    raise AssertionError(f"Unknown sym_int type: {s}")
            elif arg.type == "as_sym_float":
                f = arg.as_sym_float
                if f.type == "as_name":
                    f.as_name = replace_table[f.as_name]
                elif f.type == "as_float":
                    pass
                else:
                    raise AssertionError(f"Unknown sym_float type: {f}")
            elif arg.type in ("as_none", "as_bool", "as_int", "as_float", "as_string"):
                return
            else:
                raise AssertionError(f"Unknown input type: {arg}")
        elif spec.type == "loss_output":
            t = spec.loss_output.arg
            t.name = replace_table[t.name]
        elif spec.type == "buffer_mutation":
            t = spec.buffer_mutation.arg
            t.name = replace_table[t.name]
        elif spec.type == "parameter_mutation":
            t = spec.parameter_mutation.arg
            t.name = replace_table[t.name]
        elif spec.type == "gradient_to_parameter":
            t = spec.gradient_to_parameter.arg
            t.name = replace_table[t.name]
        elif spec.type == "gradient_to_user_input":
            g = spec.gradient_to_user_input
            g.arg.name = replace_table[g.arg.name]
            g.user_input_name = replace_table[g.user_input_name]
        elif spec.type == "user_input_mutation":
            u = spec.user_input_mutation
            u.arg.name = replace_table[u.arg.name]
            u.user_input_name = replace_table[u.user_input_name]
        elif spec.type == "token":
            tok = spec.token.arg
            tok.name = replace_table[tok.name]
        else:
            raise AssertionError(f"Unknown output type: {spec}")

    for spec in input_specs:
        replace_input(spec)

    for spec in output_specs:
        replace_output(spec)

    return ExportedProgram(
        graph_module=GraphModule(
            graph=sorted_graph,
            signature=GraphSignature(
                input_specs=list(input_specs),
                output_specs=list(output_specs),
            ),
            module_call_graph=module_call_graph,
        ),
        opset_version=opset_version,
        range_constraints=range_constraints,
        schema_version=ep.schema_version,
        verifiers=ep.verifiers,
        torch_version=ep.torch_version,
        guards_code=guards_code,
    )