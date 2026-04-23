def __init__(
        self,
        flat_graph: torch.fx.Graph,
        nodes: tuple[torch.fx.Node, ...],
        seen_nodes,
        seen_modules,
        seen_attrs,
        created_modules,
        parent,
        module_stack: list[tuple[str, str | None, int]],
        module_id,
        module_call_graph: dict[str, ModuleCallSignature],
        module: torch.fx.GraphModule | UnflattenedModule | None = None,
    ):
        self.flat_graph = flat_graph
        self.nodes = nodes
        self.seen_nodes = seen_nodes
        self.seen_modules = seen_modules
        self.seen_attrs = seen_attrs
        self.created_modules = created_modules
        self.parent = parent
        self.module_stack = module_stack
        self.module_id = module_id

        self.module_call_graph = module_call_graph
        self.verbose = False

        self.fqn, ty, num_calls = self.module_stack[-1]
        # generate call name for self.fqn
        self.child_fqn = _call_name(self.fqn, num_calls + 1)

        self.module: torch.fx.GraphModule | UnflattenedModule | InterpreterModule
        if module is not None:
            self.module = module
            self.ivals = module.ivals if hasattr(module, "ivals") else {}  # type: ignore[var-annotated]
        else:
            self.module = self.created_modules.get(
                self.fqn,
                InterpreterModule(torch.fx.Graph(), ty=ty),
            )
            self.ivals = parent.ivals

        self.graph = self.module.graph

        # Mapping of nodes in the flat graph to nodes in this graph.
        self.node_map: dict[torch.fx.Node, torch.fx.Node] = {}
        self.node_to_placeholder = {}

        self.parent_call_module: torch.fx.Node | None = None
        if parent is not None:
            accessor = _compute_accessor(parent.fqn, self.child_fqn)

            def create_module(fqn):
                path = f"{parent.fqn}.{fqn}" if parent.fqn else fqn
                if path in self.created_modules:
                    return self.created_modules[path]
                submod = InterpreterModule(torch.fx.Graph(), ty=ty)
                self.created_modules[path] = submod
                return submod

            _add_submodule(parent.module, accessor, self.module, create_module)
            self.parent_call_module = parent.graph.call_module(accessor)
            if self.seen_modules[self.module_id]:
                base_module_frame = self.seen_modules[self.module_id][0]
                self.module._modules = base_module_frame.module._modules
            self.seen_modules[self.module_id].append(
                _SubmoduleEntry(
                    parent_fqn=self.parent.fqn,
                    parent_module=self.parent.module,
                    parent_call_module=self.parent_call_module,
                    fqn=self.fqn,
                    call_idx=num_calls + 1,
                    module=self.module,
                )
            )

        signature = module_call_graph.get(self.child_fqn)
        if signature is not None and self.parent is not None:
            if signature.in_spec.num_children != 2:
                raise AssertionError(
                    f"expected in_spec to have 2 children, got {signature.in_spec.num_children}"
                )
            if signature.in_spec.type is not tuple:
                raise AssertionError(
                    f"expected in_spec.type to be tuple, got {signature.in_spec.type}"
                )
            args_spec, kwargs_spec = signature.in_spec.children()
            if args_spec.type is not tuple:
                raise AssertionError(
                    f"expected args_spec.type to be tuple, got {args_spec.type}"
                )
            if kwargs_spec.type is not dict:
                raise AssertionError(
                    f"expected kwargs_spec.type to be dict, got {kwargs_spec.type}"
                )

            with self.graph.inserting_after(None):
                arg_nodes = [
                    self.graph.placeholder(f"_positional_arg_{idx}")
                    for idx in range(args_spec.num_children)
                ]
                kwarg_nodes = {}
                for name in kwargs_spec.context:
                    kwarg_nodes[name] = self.graph.placeholder(name)
                flat_args = _generate_flatten_spec(
                    self.module,
                    (tuple(arg_nodes), kwarg_nodes),
                    signature.in_spec,
                )
                for idx, arg in enumerate(signature.inputs):
                    flat_arg_node = self.graph.create_node(
                        op="call_function",
                        target=operator.getitem,
                        args=(flat_args, idx),
                        name=(
                            arg.name
                            if not isinstance(arg, ConstantArgument)
                            else f"_constant_{idx}"
                        ),
                    )
                    if isinstance(arg, ConstantArgument):
                        continue

                    if arg.name in self.seen_nodes:
                        flat_arg_node.meta = copy.copy(self.seen_nodes[arg.name].meta)
                        self.node_to_placeholder[self.seen_nodes[arg.name]] = (
                            flat_arg_node
                        )

            with self.parent.graph.inserting_before(self.parent_call_module):
                input_nodes: list[torch.fx.Node | None] = []
                for input in signature.inputs:
                    if isinstance(input, ConstantArgument):
                        input_nodes.append(input.value)  # type: ignore[arg-type]
                    elif input.name not in self.seen_nodes:
                        input_nodes.append(None)
                    else:
                        if not isinstance(
                            input,
                            (
                                TensorArgument,
                                SymIntArgument,
                                SymBoolArgument,
                                SymFloatArgument,
                            ),
                        ):
                            raise AssertionError(
                                f"expected input to be TensorArgument, SymIntArgument, "
                                f"SymBoolArgument, or SymFloatArgument, got {type(input)}"
                            )
                        input_nodes.append(
                            self.parent.remap_input(self.seen_nodes[input.name])
                        )

                inputs_node = _generate_unflatten(
                    self.parent.module,
                    input_nodes,
                    signature.in_spec,
                )

                args_node = self.parent.graph.call_function(
                    operator.getitem, (inputs_node, 0)
                )
                kwargs_node = self.parent.graph.call_function(
                    operator.getitem, (inputs_node, 1)
                )
                arg_nodes = [
                    self.parent.graph.call_function(operator.getitem, (args_node, i))
                    for i in range(args_spec.num_children)
                ]
                kwarg_nodes = {
                    k: self.parent.graph.call_function(
                        operator.getitem, (kwargs_node, k)
                    )
                    for k in kwargs_spec.context
                }
            if self.parent_call_module is None:
                raise AssertionError("parent_call_module must not be None")
            # pyrefly: ignore [bad-assignment]
            self.parent_call_module.args = tuple(arg_nodes)
            self.parent_call_module.kwargs = kwarg_nodes