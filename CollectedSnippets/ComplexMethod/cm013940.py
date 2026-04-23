def _invoke_leaf_function_python(
    real_impl: Callable[..., Any],
    fake_impl: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    mutates_args: frozenset[str] | None = None,
    hook_fn: Callable[..., Any] | None = None,
    hook_fake_fn: Callable[..., Any] | None = None,
) -> Any:
    """Call invoke_leaf_function HOP directly from Python.

    This enables @leaf_function to work with make_fx
    without relying on Dynamo to intercept the call.
    """
    from torch._higher_order_ops.invoke_leaf_function import (
        _LeafCallable,
        convert_modules_to_states,
        invoke_leaf_function,
        make_leaf_function_wrappers,
        store_makefx_modules,
    )

    captured_modules: list[torch.nn.Module] = []
    seen_module_ids: dict[int, int] = {}  # id(module) -> position in captured_modules
    for val in pytree.tree_flatten(
        (args, kwargs), is_leaf=lambda x: isinstance(x, torch.nn.Module)
    )[0]:
        if isinstance(val, torch.nn.Module) and id(val) not in seen_module_ids:
            seen_module_ids[id(val)] = len(captured_modules)
            captured_modules.append(val)

    global_indices = store_makefx_modules(captured_modules)
    module_to_index = {
        mod_id: global_indices[pos] for mod_id, pos in seen_module_ids.items()
    }

    processed = convert_modules_to_states((args, kwargs), module_to_index)
    flat_args, input_spec = pytree.tree_flatten(processed)

    # Single-element mutable list so the wrappers can write back the output
    # TreeSpec. Read captured_out_spec[0] after the wrappers have been called.
    captured_out_spec: list[pytree.TreeSpec | None] = [None]
    wrapped_real, wrapped_fake = make_leaf_function_wrappers(
        real_impl, fake_impl, captured_out_spec
    )

    real_fn_callable = _LeafCallable(wrapped_real)
    fake_fn_callable = _LeafCallable(wrapped_fake)

    if hook_fn is not None:
        real_fn_callable._leaf_hook_real_fn = hook_fn  # type: ignore[attr-defined]
        real_fn_callable._leaf_hook_fake_fn = hook_fake_fn  # type: ignore[attr-defined]

    mutated_flat_indices = ""
    if mutates_args:
        from torch._higher_order_ops.invoke_leaf_function import (
            _resolve_mutated_flat_indices,
        )

        mutated_flat_indices = _resolve_mutated_flat_indices(
            real_impl, mutates_args, len(flat_args), input_spec
        )

    flat_out = invoke_leaf_function(
        real_fn_callable, fake_fn_callable, input_spec, mutated_flat_indices, *flat_args
    )

    assert captured_out_spec[0] is not None
    return pytree.tree_unflatten(flat_out, captured_out_spec[0])