def node_support_preview(self, dump_graph: bool = False) -> str:
        submodules = dict(self.module.named_modules())

        supported_nodes: NodeList = []
        supported_node_types = defaultdict(set)
        unsupported_node_types = defaultdict(set)

        def get_dtype(arg: torch.fx.Node) -> torch.dtype | None:
            tensor_meta = arg.meta.get("tensor_meta")
            return getattr(tensor_meta, "dtype", None)

        for node in self.module.graph.nodes:
            if node.op not in CALLABLE_NODE_OPS:
                continue

            target = get_node_target(submodules, node)

            # Store dtype of arg in node.args. If arg doesn't have dtype, i.e. not a tensor, we'll store None.
            arg_dtypes = [
                get_dtype(arg) if isinstance(arg, torch.fx.Node) else None
                for arg in node.args
            ]

            # Find last non-None element. If all elements are None, return max_len.
            last_index = len(arg_dtypes) - next(
                (
                    i
                    for i, dtype in enumerate(reversed(arg_dtypes))
                    if dtype is not None
                ),
                len(arg_dtypes),
            )

            # Strip None elements at the end.
            arg_dtypes_tuple = tuple(arg_dtypes[:last_index])
            kwarg_dtypes_tuple = tuple(
                (k, get_dtype(arg))
                for k, arg in node.kwargs.items()
                if isinstance(arg, torch.fx.Node)
            )

            if self.operator_support.is_node_supported(submodules, node):
                supported_nodes.append(node)
                supported_node_types[target].add((arg_dtypes_tuple, kwarg_dtypes_tuple))
            else:
                unsupported_node_types[target].add(
                    (arg_dtypes_tuple, kwarg_dtypes_tuple)
                )

        if dump_graph:
            self._draw_graph_based_on_node_support(self.module, supported_nodes)

        reports = "\nSupported node types in the model:\n"
        for t, dtypes in supported_node_types.items():
            for arg_dtypes_tuple, kwarg_dtypes_tuple in dtypes:
                reports += f"{t}: ({arg_dtypes_tuple}, {dict(kwarg_dtypes_tuple)})\n"

        reports += "\nUnsupported node types in the model:\n"
        for t, dtypes in unsupported_node_types.items():
            for arg_dtypes_tuple, kwarg_dtypes_tuple in dtypes:
                reports += f"{t}: ({arg_dtypes_tuple}, {dict(kwarg_dtypes_tuple)})\n"

        print(reports)

        # Return reports for testing purpose
        return reports