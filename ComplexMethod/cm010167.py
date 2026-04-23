def lift_constants_pass(
    gm: torch.fx.GraphModule,
    graph_signature: ExportGraphSignature,
    constant_attrs: ConstantAttrMap,
) -> dict[str, _ConstantAttributeType]:
    """
    Takes a graph module, graph signature, and modifies them inplace to lift any
    constants (tensors or custom classes) as inputs to the graph. Returns a
    dictionary of names to constants.

    Arguments:
        gm (torch.fx.GraphModule): The graph module containing the graph and constants to lift.
        graph_signature (ExportGraphSignature): This graph signature will be
            mutated to add additional CONSTANT_TENSOR and CUSTOM_OBJ inputs.
        constant_attrs (ConstantAttr): A mapping from a constant value to its
            fully-qualified path in `gm`. This is used to maintain consistent
            location of constants between the original module and the exported
            version.

    Returns:
        A dictionary of fqn => constant value.
    """
    all_constants: dict[str, _ConstantAttributeType] = {}

    input_specs = graph_signature.input_specs
    num_custom_obj = sum(
        input_spec.kind == InputKind.CUSTOM_OBJ for input_spec in input_specs
    )
    num_tensor_constants = sum(
        input_spec.kind == InputKind.CONSTANT_TENSOR for input_spec in input_specs
    )

    fake_mode = detect_fake_mode(
        tuple(node.meta["val"] for node in gm.graph.nodes if node.op == "placeholder")
    )

    first_user_input_loc, first_user_input = 0, next(iter(gm.graph.nodes))
    used_target_names = set()

    input_nodes = [node for node in gm.graph.nodes if node.op == "placeholder"]
    if len(input_nodes) != len(input_specs):
        raise AssertionError(
            f"input nodes count {len(input_nodes)} != input specs count {len(input_specs)}"
        )
    for i, (node, input_spec) in enumerate(zip(input_nodes, input_specs)):
        used_target_names.add(input_spec.target)
        if input_spec.kind == InputKind.USER_INPUT:
            first_user_input = node
            first_user_input_loc = i
            break

    lifted_objs = ConstantAttrMap()
    renamed_targets = {}
    for node in list(gm.graph.nodes):
        if node.op == "get_attr":
            if nodes_to_remove := _unused_constant(node):
                # Remove the node if it's not being used
                for node_rm in nodes_to_remove:
                    gm.graph.erase_node(node_rm)
                continue

            constant_val = _get_attr(gm, node.target)
            # These are not hashable and not gonna be lifted
            # so we can skip them earlier
            if isinstance(constant_val, torch.fx.GraphModule):
                continue
            if "LoweredBackendModule" in type(constant_val).__name__:
                continue
            if "AOTInductorRunnerWrapper" in type(constant_val).__name__:
                continue
            if isinstance(constant_val, torch.utils._pytree.TreeSpec):
                continue

            if constant_val in lifted_objs:
                # We already lifted this constant elsewhere. Just rewrite uses
                # of this get_attr to point to the already-existing placeholder
                # node.
                const_placeholder_node = _get_first_fqn(lifted_objs, constant_val)
                node.replace_all_uses_with(const_placeholder_node)
                gm.graph.erase_node(node)
                renamed_targets[node.name] = const_placeholder_node.name
                continue

            # For ScriptObject, Tensor and FakeScriptObject constants:
            # First check if the constant was an attribute on some module by
            # consulting `constant_attrs` map. If it is, use the fqn that keeps
            # its location consistent with the eager module.
            #
            # If it's not in the `constant_attrs` map, that means it's an inline
            # constant (e.g. x + torch.tensor(0)), and thus did not have a
            # specific location in the eager module. In that case, just generate
            # some name and attach it to the module in which it was used.
            if isinstance(
                constant_val, (torch.ScriptObject, FakeScriptObject)
            ) or is_opaque_reference_type(type(constant_val)):
                constant_kind = InputKind.CUSTOM_OBJ
                constant_fqn = _get_first_fqn(constant_attrs, constant_val)
                if constant_fqn is not None:
                    constant_name = constant_fqn.replace(".", "_")
                else:
                    constant_name = f"lifted_custom_{num_custom_obj}"
                    constant_fqn = get_constant_fqn(node, constant_name)
                    while constant_fqn in used_target_names:
                        num_custom_obj += 1
                        constant_name = f"lifted_custom_{num_custom_obj}"
                        constant_fqn = get_constant_fqn(node, constant_name)
                    num_custom_obj += 1
            elif isinstance(constant_val, torch.Tensor):
                # Remove the parameterness of constant_val
                if isinstance(constant_val, torch.nn.Parameter):
                    log.debug(
                        "%s created when tracing %s is a parameter. But "
                        "it's not registered with register_parameter(). export will treat it as a constant tensor",
                        str(node.target),
                        str(node.meta.get("stack_trace", "<unknown stack>")),
                    )
                    # We get the real data out of the parameter by disabling the surrounding fake mode.
                    with unset_fake_temporarily():
                        constant_val = constant_val.data
                constant_kind = InputKind.CONSTANT_TENSOR
                constant_fqn = _get_first_fqn(constant_attrs, constant_val)
                if constant_fqn is not None:
                    constant_name = constant_fqn.replace(".", "_")
                else:
                    constant_name = f"lifted_tensor_{num_tensor_constants}"
                    constant_fqn = get_constant_fqn(node, constant_name)
                    while constant_fqn in used_target_names:
                        num_tensor_constants += 1
                        constant_name = f"lifted_tensor_{num_tensor_constants}"
                        constant_fqn = get_constant_fqn(node, constant_name)
                    num_tensor_constants += 1
            else:
                raise SpecViolationError(
                    f"getattr node {node} referencing unsupported type {type(constant_val)}"
                )

            with gm.graph.inserting_before(first_user_input):
                # Insert the constant node before the first user input
                const_placeholder_node = gm.graph.placeholder(constant_name)
                # match target name with its node name in case there is name collision
                # and suffix is added to node name in fx
                const_placeholder_node.target = const_placeholder_node.name

                for k, v in node.meta.items():
                    const_placeholder_node.meta[k] = v

                # Once the FQN has been used, remove nn_module_stack, stack_trace
                const_placeholder_node.meta.pop("nn_module_stack")
                const_placeholder_node.meta.pop("stack_trace", None)

                input_spec_arg: ArgumentSpec
                if isinstance(constant_val, torch.Tensor):
                    if fake_mode is not None:
                        const_placeholder_node.meta["val"] = fake_mode.from_tensor(
                            constant_val, static_shapes=True
                        )
                        const_placeholder_node.meta["val"].constant = constant_val
                    else:
                        const_placeholder_node.meta["val"] = constant_val
                    input_spec_arg = TensorArgument(name=const_placeholder_node.name)
                elif isinstance(constant_val, torch._C.ScriptObject):
                    class_fqn = constant_val._type().qualified_name()  # type: ignore[attr-defined]
                    const_placeholder_node.meta["val"] = CustomObjArgument(
                        constant_fqn, class_fqn
                    )
                    input_spec_arg = CustomObjArgument(
                        name=const_placeholder_node.name, class_fqn=class_fqn
                    )
                elif isinstance(constant_val, FakeScriptObject):
                    class_fqn = constant_val.script_class_name
                    const_placeholder_node.meta["val"] = CustomObjArgument(
                        constant_fqn, class_fqn, constant_val
                    )
                    input_spec_arg = CustomObjArgument(
                        name=const_placeholder_node.name,
                        class_fqn=class_fqn,
                        fake_val=constant_val,
                    )
                elif is_opaque_type(type(constant_val)):
                    class_fqn = get_opaque_type_name(type(constant_val))
                    fake_val = (
                        maybe_to_fake_obj(fake_mode, constant_val)
                        if fake_mode
                        else None
                    )
                    const_placeholder_node.meta["val"] = CustomObjArgument(
                        constant_fqn,
                        class_fqn,
                        fake_val,  # pyrefly: ignore[bad-argument-type]
                    )
                    input_spec_arg = CustomObjArgument(
                        name=const_placeholder_node.name,
                        class_fqn=class_fqn,
                        fake_val=fake_val,  # pyrefly: ignore[bad-argument-type]
                    )
                else:
                    raise SpecViolationError(
                        f"tried to lift unsupported type {type(constant_val)} from node {node.format_node()}"
                    )

                lifted_objs.add(constant_val, const_placeholder_node)
                node.replace_all_uses_with(const_placeholder_node)
                gm.graph.erase_node(node)

                renamed_targets[node.name] = const_placeholder_node.name

                # Add the constant as a buffer to the graph signature
                graph_signature.input_specs.insert(
                    first_user_input_loc,
                    InputSpec(
                        kind=constant_kind,
                        arg=input_spec_arg,
                        target=constant_fqn,
                    ),
                )
                if constant_val in constant_attrs:
                    for fqn in constant_attrs[constant_val]:
                        all_constants[fqn] = constant_val
                else:
                    all_constants[constant_fqn] = constant_val
                first_user_input_loc += 1

    for spec in graph_signature.output_specs:
        if spec.arg.name in renamed_targets:
            spec.arg.name = renamed_targets[spec.arg.name]

    return all_constants