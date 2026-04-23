def forward(*args, **kwargs):
        effective_keys = include_keys
        if include_keys.has(DispatchKey.PythonDispatcher):
            effective_keys = effective_keys.remove(DispatchKey.PythonDispatcher)
        if effective_keys.has(DispatchKey.Python):
            effective_keys = effective_keys.remove(DispatchKey.Python)
        with torch._C._ForceDispatchKeyGuard(effective_keys, exclude_keys):
            with torch.enable_grad():
                outputs = fn(*args, **kwargs)

                flat_inputs = flatten_args_with_modules((args, kwargs))
                requires_grad_indices = {
                    i
                    for i, inp in enumerate(flat_inputs)
                    if isinstance(inp, torch.Tensor) and inp.requires_grad
                }
                check_escaped_gradients(outputs, flat_inputs, requires_grad_indices)

                state["inputs"] = tuple(
                    GradientInfo(
                        edge=get_gradient_edge(inp),
                        size=inp.size(),
                        stride=inp.stride(),
                        dtype=inp.dtype,
                        device=inp.device,
                    )
                    if isinstance(inp, torch.Tensor) and inp.requires_grad
                    else None
                    for inp in flat_inputs
                )

                if outputs is None:
                    state["outputs"] = ()
                else:
                    state["outputs"] = tuple(
                        GradientInfo(
                            edge=get_gradient_edge(out),
                            size=out.size(),
                            stride=out.stride(),
                            dtype=out.dtype,
                            device=out.device,
                        )
                        if isinstance(out, torch.Tensor)
                        and out.requires_grad
                        and out.grad_fn is not None
                        else None
                        for out in outputs
                    )

        return pytree.tree_map_only(
            torch.Tensor,
            lambda t: t.detach().requires_grad_(t.requires_grad),
            outputs,
        )