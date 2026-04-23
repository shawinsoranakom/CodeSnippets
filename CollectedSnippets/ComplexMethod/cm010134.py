def placeholder_naming_pass(
    gm: torch.fx.GraphModule,
    export_graph_signature: "ExportGraphSignature",
    mod: torch.nn.Module,
    fake_args,
    fake_kwargs,
    fake_params_buffers,
    constants: dict[str, Any],
) -> None:
    """
    This pass is run at the end of _export_non_strict() to assign better placeholder node names:
        - User inputs:
            These follow the signature of mod.forward(), e.g. forward(x, y) produces nodes x, y.
            For nested inputs from dictionaries, lists, tuples, or dataclasses,
            the names are a concatenation of the path to the tensor.
                e.g. x = {
                    'a': torch.randn(),
                    'b': [torch.randn(), torch.randn()]
                }
            produces nodes x_a, x_b_0, x_b_1.
        - Parameters/buffers/constants/custom objects:
            These follow the FQN of the object, prefixed by "p", "b", "c", "obj" respectively.
                e.g. self.bar.l0.weight produces "p_bar_l0_weight".
        - Effect tokens:
            These are named token, token_1, ...
    """

    custom_meta: dict[str, Any] = {}
    if isinstance(mod, torch.fx.GraphModule):
        for node in mod.graph.nodes:
            if "custom" in node.meta:
                custom_meta[node.name] = node.meta["custom"]

    def _strip_name(x):
        if x.startswith("L__self___"):
            x = x[len("L__self___") :]
        elif x.startswith("self_"):
            x = x[len("self_") :]
        x = re.sub(r"[^a-zA-Z0-9]", "_", x)
        return x

    def _extract_pytree_key(x):
        if isinstance(x, MappingKey):
            x = re.sub(r"[^a-zA-Z0-9]", "_", str(x.key))
            return x
        elif isinstance(x, SequenceKey):
            return str(x.idx)
        elif isinstance(x, GetAttrKey):
            return x.name
        else:
            raise RuntimeError(f"Pytree key of type {type(x)} not handled for {x}")

    name_map: dict[str, str] = {}
    find_available: dict[str, int] = defaultdict(int)
    used_names: set[str] = set()

    # map user input names with mod.forward() signature
    combined_args = _bind_signature_to_inputs(mod, fake_args, fake_kwargs)

    flat_args_with_path, _ = tree_flatten_with_path(combined_args)
    user_input_names = [
        spec.arg.name
        for spec in export_graph_signature.input_specs
        if spec.kind == InputKind.USER_INPUT
    ]

    # use pytree path to name nested user inputs
    for (arg_path, _arg), user_input_name in zip(flat_args_with_path, user_input_names):
        if user_input_name:
            _rename_without_collisions(
                name_map,
                find_available,
                used_names,
                user_input_name,
                placeholder_prefixes[InputKind.USER_INPUT]
                + "_".join(_extract_pytree_key(x).lower() for x in arg_path),
                is_placeholder=True,
            )

    # use graph signature input specs to map param/buffer/constant names
    # name effect tokens as token, token_1, ... (these aren't visible to user)
    for spec in export_graph_signature.input_specs:
        if spec.kind == InputKind.USER_INPUT:
            continue
        if spec.kind == InputKind.TOKEN:
            base_name = ""
        else:
            base_name = _strip_name(spec.target).lower()
        base_name = re.sub(r"[^a-zA-Z0-9]", "_", base_name)

        _rename_without_collisions(
            name_map,
            find_available,
            used_names,
            spec.arg.name,
            placeholder_prefixes[spec.kind] + base_name,
            is_placeholder=True,
        )
        if base_name in custom_meta:
            # the keys in custom_meta are node names from `mod`,
            # which is the base_name here.
            # we need the re-mapped name for lookup later
            custom_meta[name_map[spec.arg.name]] = custom_meta[base_name]
            del custom_meta[base_name]

    # handle naming collisions with call_function/get_attr inputs.
    # here, we want to prioritize user input names over call_function names
    # e.g. not have forward(self, mul): lead to a placeholder node called mul_13,
    # so we increment the suffix of call_function nodes as needed
    for node in gm.graph.nodes:
        if node.op == "placeholder":
            continue
        _rename_without_collisions(
            name_map, find_available, used_names, node.name, node.name
        )

    # assign new node names
    _assign_new_node_names(gm, name_map, custom_meta)

    # propagate names to higher order op subgraphs
    _name_hoo_subgraph_placeholders(gm)

    # re-generate graph module code
    gm.recompile()

    # modify graph signature (input specs, output specs, user input mutations)
    for spec in export_graph_signature.input_specs:
        if spec.arg.name not in name_map:
            raise AssertionError(f"input spec arg {spec.arg.name!r} not in name_map")
        spec.arg.name = name_map[spec.arg.name]
        if (  # handle targets for custom objects
            spec.kind == InputKind.CUSTOM_OBJ and spec.target in name_map
        ):
            # pyrefly: ignore [bad-index, index-error]
            spec.target = name_map[spec.target][4:]  # strip obj_ prefix

    for spec in export_graph_signature.output_specs:
        if spec.arg.name in name_map:
            spec.arg.name = name_map[spec.arg.name]
        if spec.kind == OutputKind.USER_INPUT_MUTATION and spec.target in name_map:
            # pyrefly: ignore [bad-index, index-error]
            spec.target = name_map[spec.target]

    # rename keys in constants dict for custom objects
    for name in list(constants.keys()):
        constant = constants[name]
        if name in name_map and not isinstance(
            constant, torch.Tensor
        ):  # rename custom objects with generic names
            new_name = name_map[name]
            if (
                new_name != name
                and re.match(r"arg(\d+)_1", name)
                and new_name != placeholder_prefixes[InputKind.CUSTOM_OBJ] + name
            ):
                constants[new_name] = constant
                del constants[name]