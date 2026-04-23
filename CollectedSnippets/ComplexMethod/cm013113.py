def _exported_program_to_onnx_program(
    exported_program: torch.export.ExportedProgram,
    *,
    registry: _registration.ONNXRegistry,
    lower: Literal["at_conversion", "none"] = "at_conversion",
) -> _onnx_program.ONNXProgram:
    """Convert an exported program to an ONNX Program.

    The exported_program field in the returned ONNXProgram is one that is after
    decompositions have been applied.

    Reference:
        - ExportedProgram spec: https://pytorch.org/docs/stable/export.ir_spec.html

    Args:
        exported_program: The exported program to convert. The exported program
            should be the one that is after decompositions have been applied.
        lower: Whether to lower the graph to core ONNX operators.
            at_conversion: Lower when translating the FX graph to ONNX IR.
            none: Do not lower the graph.
        registry: The registry of all ONNX Script decomposition.
    """
    model = ir.Model(
        graph=ir.Graph(
            [],
            [],
            nodes=[],
            # Opset imports are added to the model in the final add_opset_imports pass
            name="main_graph",
            metadata_props={
                "pkg.torch.export.ExportedProgram.graph_signature": str(
                    exported_program.graph_signature
                ),
                "pkg.torch.export.ExportedProgram.range_constraints": str(
                    exported_program.range_constraints
                ),
            },
        ),
        ir_version=_constants.ONNX_IR_VERSION,
        producer_name="pytorch",
        producer_version=torch.__version__,
    )

    # A dictionary storing the translated subgraphs as ONNX functions made available to outer graphs
    # {<subgraph_scope>: {<subgraph_name>: <IR function>}}
    scoped_subgraphs: dict[str, dict[str, ir.Function]] = {}
    values = None

    # 1. Translate all nodes in all subgraphs and the main graph
    # Create a dictionary of values for the main graph for step 2-3 to add inputs and outputs
    module: torch.fx.GraphModule
    # Reverse the order of the modules so that the innermost module is processed first
    # and made available to the outer module
    for name, module in reversed(
        tuple(exported_program.graph_module.named_modules(remove_duplicate=False))
    ):
        # Obtain the graphs (previously built) owned by the current module
        owned_graphs = scoped_subgraphs.setdefault(name, {})
        fx_graph = module.graph

        graph_like: ir.Graph | ir.Function
        if name == "":
            # Root graph
            graph_like = model.graph
        else:
            function_name = name.replace(".", "__")
            # Inputs and outputs will be created within _translate_fx_graph
            func = ir.Function(
                domain=_constants.LOCAL_FUNCTION_DOMAIN,
                name=function_name,
                graph=ir.Graph((), (), nodes=()),
                attributes=(),
            )
            # Make this function available to the outer graph
            scope, subgraph_name = _get_scope_name(name)
            scoped_subgraphs.setdefault(scope, {})[subgraph_name] = func
            model.functions[func.identifier()] = func
            graph_like = func

        values = _translate_fx_graph(
            fx_graph,
            model,
            graph_like=graph_like,
            owned_graphs=owned_graphs,
            lower=lower,
            registry=registry,
        )

    if name != "":
        raise AssertionError("The last module processed should be the root module")
    if values is None:
        raise AssertionError("values must be non-None")

    # Clear the input/output of the main graph and add them back in step 2-3
    # using the more accurate graph signature
    model.graph.inputs.clear()
    model.graph.outputs.clear()

    # 2. Add user inputs and all parameters/buffers to the graph.
    # Since the node names and the tensor names are different, we need to rename
    # the nodes to match the tensor names later. For now we will just use the node names.
    user_inputs = [
        spec
        for spec in exported_program.graph_signature.input_specs
        if spec.kind == graph_signature.InputKind.USER_INPUT
    ]
    non_user_inputs = [
        spec
        for spec in exported_program.graph_signature.input_specs
        if spec.kind != graph_signature.InputKind.USER_INPUT
    ]

    for spec in itertools.chain(user_inputs, non_user_inputs):
        # Put the user inputs first and then the parameters/buffers
        if isinstance(spec.arg, graph_signature.ConstantArgument):
            logger.debug("Skipping constant argument %s", spec.arg)
            continue
        value_name = spec.arg.name
        input_kind = spec.kind
        persistent = spec.persistent
        value = values[value_name]

        if isinstance(value, Sequence):
            raise AssertionError(
                f"Input '{value_name}' should not be a sequence. This is unexpected."
            )

        value.metadata_props["pkg.torch.export.graph_signature.InputSpec.kind"] = (
            input_kind.name
        )
        value.metadata_props[
            "pkg.torch.export.graph_signature.InputSpec.persistent"
        ] = str(persistent)

        if input_kind == graph_signature.InputKind.USER_INPUT:
            # Add only user inputs to the graph
            # Subsequent passes can decide if they want to add initializers as inputs
            model.graph.inputs.append(value)
        else:
            model.graph.initializers[value_name] = value

    # 3. Add user outputs to the graph and assign metadata to all outputs
    user_outputs = [
        spec
        for spec in exported_program.graph_signature.output_specs
        if spec.kind == graph_signature.OutputKind.USER_OUTPUT
    ]
    non_user_outputs = [
        spec
        for spec in exported_program.graph_signature.output_specs
        if spec.kind != graph_signature.OutputKind.USER_OUTPUT
    ]
    for spec in itertools.chain(user_outputs, non_user_outputs):
        if isinstance(spec.arg, graph_signature.ConstantArgument):
            logger.warning("Skipping constant argument %s", spec.arg)
            continue
        value_name = spec.arg.name
        output_kind = spec.kind
        value = values[value_name]

        if not isinstance(value, (ir.Value, Sequence)):
            raise TypeError(
                f"Output '{value_name}' should be an ir.Value. Actual type is '{type(value)}': {value!r}. "
                "This may be due to an incorrect implementation of the ONNX function that produced this output."
            )

        # The output value may be a sequence, meaning the operator has multiple outputs
        _values = (value,) if not isinstance(value, Sequence) else value

        if len(_values) > 1:
            logger.warning(
                "Model output '%s' has multiple values: %s (output spec: %s). Please make sure this is expected.",
                value_name,
                _values,
                spec,
            )

        for value in _values:
            value.metadata_props["pkg.torch.export.graph_signature.OutputSpec.kind"] = (
                output_kind.name
            )
            if output_kind == graph_signature.OutputKind.USER_OUTPUT:
                model.graph.outputs.append(value)

    # 4. Rename the initializers to match the tensor names
    for name, param_name in itertools.chain(
        exported_program.graph_signature.inputs_to_parameters.items(),
        exported_program.graph_signature.inputs_to_buffers.items(),
        exported_program.graph_signature.inputs_to_lifted_tensor_constants.items(),
    ):
        initializer = model.graph.initializers.pop(name)
        initializer.name = param_name
        # Record the original name so users can search the metadata and correspond
        # with the FX graph
        initializer.metadata_props["pkg.torch.onnx.original_node_name"] = name
        model.graph.initializers[param_name] = initializer

    # 5. Add initializers to the graph
    # ExportedProgram stores parameters and buffers in state_dict,
    # but non_persistent_buffers and lifted_tensor_constants are not there
    # so we need to get them from the name_* apis.
    for name, torch_tensor in itertools.chain(
        exported_program.named_parameters(),
        # pyrefly: ignore [bad-argument-type]
        exported_program.named_buffers(),
        exported_program.constants.items(),
    ):
        initializer = model.graph.initializers.get(name)  # type: ignore[assignment]
        if initializer is None:
            logger.warning("Tensor '%s' is not one of the initializers", name)
            continue
        if not isinstance(torch_tensor, torch.Tensor):
            raise NotImplementedError(
                f"Tensor '{name}' should be a torch.Tensor. Actual type is '{type(torch_tensor)}': {torch_tensor!r}. "
                "This is unexpected and not yet supported."
            )

        # Turn complex tensors into float tensors when converting to ONNX
        complex_to_float = lower != "none"
        if complex_to_float:
            if torch_tensor.dtype.is_complex:
                torch_tensor = torch.view_as_real(torch_tensor)

        ir_tensor = TorchTensor(torch_tensor, name=name)
        initializer.const_value = ir_tensor
        _set_shape_type(
            initializer,
            torch_tensor,
            complex_to_float=complex_to_float,
        )

    # TODO: Decide if we should keep mutated buffers as inputs/outputs

    # Collect and add opset imports to the model
    _ir_passes.add_opset_imports(model)

    return _onnx_program.ONNXProgram(model, exported_program)