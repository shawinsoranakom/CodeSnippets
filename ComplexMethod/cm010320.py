def __init__(
        self,
        export_module: ExportedProgram,
        flat_args_adapter: FlatArgsAdapter | None = None,
    ):
        super().__init__()
        if export_module.graph_signature.backward_signature is not None:
            raise ValueError("Unflattening on JointExportModule NYI")

        def _id(obj):
            """Returns _TensorID dataclass for tensors, otherwise id()."""
            if isinstance(obj, torch.Tensor):
                return _TensorID(
                    untyped_storage=obj.untyped_storage(),
                    stride=obj.stride(),
                    size=obj.size(),
                    storage_offset=obj.storage_offset(),  # type: ignore[arg-type]
                )
            return id(obj)

        fqn_list = [entry.fqn for entry in export_module.module_call_graph]
        if fqn_list[0] != "":
            raise AssertionError(
                f"expected first fqn to be empty string, got {fqn_list[0]!r}"
            )
        export_graph = deepcopy(export_module.graph)
        self.graph_signature = deepcopy(export_module.graph_signature)
        self.graph = torch.fx.Graph()
        self.graph.owning_module = self  # type: ignore[assignment]
        self.module_call_graph = deepcopy(export_module.module_call_graph)
        self.flat_args_adapter = flat_args_adapter

        self.meta = export_module.graph_module.meta
        self.meta["unflattened_module"] = self

        # Flag to indicate whether args have been adapted.
        self.adapted = False
        self._run_with_interpreter = RUN_WITH_INTERPRETER

        _inplace_buffer_and_input_mutations(export_graph, self.graph_signature)
        _fix_nn_module_stacks(export_graph)
        self._ty = _root_module_type(export_graph)

        self.ivals = _IVals()
        # for any intermediate value of a mutation that is read, track the mutation
        seen_modules, seen_attrs = _outline_submodules(export_graph, self)
        # for each read intermediate value of a mutation, find where it was created,
        # and perform the mutation
        self.ivals.update(seen_modules.values())
        # move attributes that correspond to graph arguments for HOPs
        # from exported program to unflattened submodules
        _copy_graph_attrs(export_module._graph_module, self, seen_attrs)

        self.range_constraints = export_module.range_constraints
        self.equality_constraints: list = []

        # aliasing/unused param or buffer issues:
        # in strict-mode export, dynamo export will deduplicate aliased tensors,
        # and ignore unused tensors. For aliasing, this causes issues when some aliases
        # are unused, and we're unable to match the placeholder node to the correct FQN.
        # This leads to the graph signature potentially having the wrong target FQN,
        # and downstream issues where parameters are assigned to the wrong target attribute,
        # mismatching the relevant placeholder node in the unflattened module.
        # To resolve this we restore (_assign_attr) all aliased/unused tensors in
        # the state_dict as module attributes, but only keep the used tensors in the
        # graph's forward pass (_sink_params).
        state_dict = export_module.state_dict
        assigned_params: set[str] = set()  # tracking unused params
        id_to_param: dict[
            int | _TensorID, torch.nn.Parameter
        ] = {}  # handling weight-sharing
        for name in self.graph_signature.parameters:  # this loop adds used params
            param = state_dict[name]
            if _id(param) not in id_to_param:
                id_to_param[_id(param)] = torch.nn.Parameter(
                    param.clone(), requires_grad=param.requires_grad
                )

            _assign_attr(
                id_to_param[_id(param)],
                self,
                name,
                attr_kind=_AttrKind.PARAMETER,
            )
            assigned_params.add(name)

        non_persistent_buffers = set(self.graph_signature.non_persistent_buffers)
        assigned_buffers: set[str] = set()  # tracking unused buffers
        id_to_buffer: dict[int | _TensorID, tuple[torch.nn.Parameter, bool]] = {}
        for name in self.graph_signature.buffers:  # this loop adds used buffers
            if name in non_persistent_buffers:
                persistent = False
                buffer = export_module.constants[name]
            else:
                persistent = True
                buffer = state_dict[name]

            if _id(buffer) not in id_to_buffer:
                id_to_buffer[_id(buffer)] = (buffer.clone(), persistent)

            _assign_attr(
                id_to_buffer[_id(buffer)][0],
                self,
                name,
                attr_kind=_AttrKind.BUFFER,
                persistent=persistent,
            )
            assigned_buffers.add(name)

        # restore aliased/unused params and buffers
        # these appear in state dict but not graph signature
        for name, tensor in state_dict.items():
            if name in assigned_params or name in assigned_buffers:  # already assigned
                continue

            is_buffer = False
            if _id(tensor) in id_to_buffer or not isinstance(
                tensor, torch.nn.Parameter
            ):  # aliased buffer
                is_buffer = True

            if is_buffer:
                if (
                    _id(tensor) not in id_to_buffer
                ):  # this is completely unused (not weight-sharing)
                    id_to_buffer[_id(tensor)] = (
                        tensor,
                        True,
                    )  # assign to respect original model
                _assign_attr(
                    id_to_buffer[_id(tensor)][0],
                    self,
                    name,
                    attr_kind=_AttrKind.BUFFER,
                    persistent=True,
                )
            else:
                if _id(tensor) not in id_to_param:  # this is unused
                    id_to_param[_id(tensor)] = tensor
                _assign_attr(
                    id_to_param[_id(tensor)],
                    self,
                    name,
                    attr_kind=_AttrKind.PARAMETER,
                )

        # use id map so we don't double-clone aliased constants
        id_to_const: dict[int | _TensorID, torch.Tensor | torch._C.ScriptObject] = {}
        for fqn, constant in export_module.constants.items():
            if _id(constant) not in id_to_const:
                if isinstance(constant, torch.Tensor):
                    constant = constant.clone()
                id_to_const[_id(constant)] = constant
            _constant = id_to_const[_id(constant)]
            _assign_attr(
                _constant,
                self,
                fqn,
                attr_kind=_AttrKind.CONSTANT,
            )

        # This is to handle parameters/buffers that point to the same tensor
        # object id -> list of (node_name, target_name)
        consts_map: dict[int | _TensorID, list[tuple[str, str]]] = defaultdict(list)
        consts_targets: set[str] = set()

        def add_to_consts_map(obj_id, node_name, target_name):
            name_list = consts_map[obj_id]
            name_list.append((node_name, target_name))

        # track aliased/unused params, buffers
        # prefer using untyped_storage() over id() when it's available
        added_params_buffers: set[str] = set()
        for s in self.graph_signature.input_specs:
            if s.kind == InputKind.PARAMETER or (
                s.kind == InputKind.BUFFER and s.persistent
            ):
                if not hasattr(s.arg, "name"):
                    raise AssertionError(
                        f"expected s.arg to have 'name' attribute, got {type(s.arg)}"
                    )
                if not isinstance(s.target, str):
                    raise AssertionError(
                        f"expected s.target to be str, got {type(s.target)}"
                    )
                add_to_consts_map(
                    _id(export_module.state_dict[s.target]),
                    s.arg.name,
                    s.target,
                )
                consts_targets.add(s.target)
                added_params_buffers.add(s.target)
            elif (
                s.kind == InputKind.BUFFER
                and not s.persistent
                or s.kind == InputKind.CONSTANT_TENSOR
                or s.kind == InputKind.CUSTOM_OBJ
            ):
                if not hasattr(s.arg, "name"):
                    raise AssertionError(
                        f"expected s.arg to have 'name' attribute for kind {s.kind}, got {type(s.arg)}"
                    )
                if not isinstance(s.target, str):
                    raise AssertionError(
                        f"expected s.target to be str for kind {s.kind}, got {type(s.target)}"
                    )
                add_to_consts_map(
                    _id(export_module.constants[s.target]),
                    s.arg.name,
                    s.target,
                )
                consts_targets.add(s.target)

        # add constants that are aliased and don't appear in graph signature
        for const_name, const in export_module.constants.items():
            if const_name not in consts_targets:
                const_id = _id(const)
                if const_id not in consts_map:
                    raise AssertionError(
                        f"constant {const_name!r} id not found in consts_map"
                    )
                ph_name, _ = consts_map[const_id][0]
                add_to_consts_map(const_id, ph_name, const_name)
                added_params_buffers.add(s.target)

        # add aliased/unused params and buffers that don't appear in graph signature
        for fqn, tensor in export_module.state_dict.items():
            if fqn not in added_params_buffers:
                tensor_id = _id(tensor)
                if tensor_id not in consts_map:
                    # completely unused (no weight-sharing), ignore.
                    # this weight doesn't appear in graph module,
                    # so won't cause FQN assignment issues
                    continue
                ph_name, _ = consts_map[tensor_id][0]
                add_to_consts_map(tensor_id, ph_name, fqn)

        # node name -> list of possible targets
        inputs_to_state: dict[str, list[str]] = {}
        for node_target in consts_map.values():
            targets = [t[1] for t in node_target]
            for n, _ in node_target:
                inputs_to_state[n] = targets

        _sink_params(self, inputs_to_state, [])

        redirected_call_indices = _deduplicate_modules(seen_modules.values())
        fqn_list = [fqn for fqn in fqn_list if fqn not in redirected_call_indices]

        self._dispatch_modules(redirected_call_indices, consts_targets)
        fqn_list = [fqn for fqn in fqn_list if "@" not in fqn]

        # Cache so we don't have to compute this every time.
        # NOTE: this needs to be kept in sync with the placeholders in
        # self.graph, but currently we have no way to guarantee that.
        self.input_placeholders = [
            node for node in self.graph.nodes if node.op == "placeholder"
        ]
        self.check_input_constraints = True
        # TODO(zhxchen17) We can register modules ahead of time instead of reorder later.
        fqn_order = {fqn: i for i, fqn in enumerate(fqn_list)}
        # In the case of legacy IR, we might be missing some modules from metadata.
        for name, _ in self.named_modules(remove_duplicate=False):
            if name not in fqn_order:
                fqn_order[name] = len(fqn_order)
        _reorder_submodules(self, fqn_order)
        self.graph.lint()
        self.finalize()