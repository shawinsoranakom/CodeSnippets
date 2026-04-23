def _node_metadata_hook(
        node: torch.fx.Node,
        stack_trace: str | None = None,
        nn_module_stack: dict[str, Any] | None = None,
        custom: dict[str, Any] | None = None,
        skip_val: bool = False,
    ) -> None:
        if not skip_val:
            fake_args = pytree.tree_map(
                lambda arg: (
                    _get_example_value(arg) if isinstance(arg, torch.fx.Node) else arg
                ),
                node.args,
            )
            try:
                target = node.target
                if node.op == "call_method":
                    if not isinstance(node.target, str):
                        raise AssertionError(
                            f"Expected str target, got {type(node.target)}"
                        )
                    target = getattr(fake_args[0], node.target)
                    fake_args = fake_args[1:]
                node.meta[val_key] = target(*fake_args)  # type: ignore[operator]
            except NotImplementedError:
                # This can happen when attempting to reify a symbol with an unsupported call_function node,
                # e.g. with NestedTensors + sym_size.int via match_symbol().
                # This seems to be fine, as the node gets CSE'd and deleted later in favor of a SymInt graph input.
                pass
        if stack_trace is not None:
            node.meta["stack_trace"] = stack_trace
        if nn_module_stack is not None:
            node.meta["nn_module_stack"] = nn_module_stack
        if custom is not None:
            node.meta["custom"] = custom