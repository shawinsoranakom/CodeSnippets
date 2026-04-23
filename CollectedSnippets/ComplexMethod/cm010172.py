def _node_metadata_hook(
    node: torch.fx.Node,
    metadata: dict[str, Any] | None = None,
    fake_mode: FakeTensorMode | None = None,
) -> None:
    """
    Hook for adding the appropriate metadata to nodes that are created during a
    pass using graph.create_node. An example of how to use it:

    ```
    with _set_node_metadata_hook(gm,
        functools.partial(_node_metadata_hook, metadata={"stack_trace": "file"})
    ):
        pass(gm)
    ```

    This hook should not work for all generic cases -- specifically it assumes
    that nodes being added are only call_function nodes, and copies over the
    first argument node's nn_module_stack.
    """
    # pyrefly: ignore [bad-assignment]
    fake_mode = fake_mode or contextlib.nullcontext()

    if node.op != "call_function" or not callable(node.target):
        raise AssertionError(f"node: {node}, target: {node.target}")

    if (
        isinstance(node.target, torch._ops.OpOverload)
        and len(node.target._schema.returns) == 0
    ):
        node.meta["val"] = None
    else:
        fake_args, fake_kwargs = pytree.tree_map_only(
            torch.fx.Node, lambda arg: arg.meta["val"], (node.args, node.kwargs)
        )
        # pyrefly: ignore [bad-context-manager]
        with fake_mode, enable_python_dispatcher():
            fake_res = node.target(*fake_args, **fake_kwargs)
        node.meta["val"] = fake_res

    if metadata is not None:
        for k, v in metadata.items():
            node.meta[k] = v

    # Copy over metadata from argument nodes
    arg_meta = [
        arg.meta
        for arg in pytree.tree_flatten((node.args, node.kwargs))[0]
        if isinstance(arg, torch.fx.Node)
    ]
    if len(arg_meta) == 0:
        return
    arg_meta = arg_meta[0]

    node.meta["nn_module_stack"] = node.meta.get(
        "nn_module_stack",
        arg_meta.get(
            "nn_module_stack",
            {
                _EMPTY_NN_MODULE_STACK_KEY: (
                    _EMPTY_NN_MODULE_STACK_KEY,
                    _EMPTY_NN_MODULE_STACK_KEY,
                )
            },
        ),
    )

    node.meta["torch_fn"] = node.meta.get(
        "torch_fn",
        (
            f"{node.target.__name__}_0",
            f"{node.target.__class__.__name__}.{node.target.__name__}",
        ),
    )

    node.meta["custom"] = node.meta.get("custom", arg_meta.get("custom", {}))