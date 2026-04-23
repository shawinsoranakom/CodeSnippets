def process_forward_inputs(self, *args, **kwargs):
        signature = self.module_call_graph[0].signature

        reordered_kwargs = kwargs
        if kwargs:
            reordered_kwargs = reorder_kwargs(kwargs, signature.in_spec)

        flat_args_with_path, in_spec = pytree.tree_flatten_with_path(
            (args, reordered_kwargs)
        )
        flat_args = [x[1] for x in flat_args_with_path]

        if is_fx_symbolic_tracing():
            return flat_args

        if in_spec != signature.in_spec:
            if not self.adapted:
                print(
                    "Input treespec does not match with exported module's: \n"
                    f"Input treespec: {in_spec}. ",
                    f"Exported module treespec: {signature.in_spec}",
                )
                print("Adapting flat arg to match exported module's treespec")
            flat_args = self._adapt_flat_args(flat_args, in_spec, args)
            self.adapted = True

        if self.check_input_constraints:
            # Import here to avoid an unfortunate circular dependency.
            # TODO(suo): untangle this.
            from torch._export.utils import _check_input_constraints_for_graph

            if self.adapted is True:
                flat_arg_paths = (
                    self.flat_args_adapter.get_flat_arg_paths()
                    if self.flat_args_adapter
                    else []
                )
                if flat_arg_paths and len(flat_arg_paths) != len(flat_args):
                    raise AssertionError(
                        f"flat_arg_paths length {len(flat_arg_paths)} does not match flat_args length {len(flat_args)}"
                    )
                new_flat_args_with_path = [  # type: ignore[var-annotated]
                    (
                        (
                            SequenceKey(idx=idx),
                            GetAttrKey(
                                name=flat_arg_paths[idx]
                                if flat_arg_paths
                                else "<unknown location>"
                            ),
                        ),
                        arg,
                    )
                    for idx, arg in enumerate(flat_args)
                ]
            else:
                new_flat_args_with_path = flat_args_with_path  # type: ignore[assignment]

            _check_input_constraints_for_graph(
                self.input_placeholders, new_flat_args_with_path, self.range_constraints
            )

        return flat_args