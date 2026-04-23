def forward(
        ctx,
        real_fn_callable,
        fake_fn_callable,
        input_spec,
        mutated_arg_indices,
        *flat_args,
    ):
        include_keys = torch._C._dispatch_tls_local_include_set()
        exclude_keys = torch._C._dispatch_tls_local_exclude_set()

        requires_grad_indices = ",".join(
            str(i)
            for i, arg in enumerate(flat_args)
            if isinstance(arg, torch.Tensor) and arg.requires_grad
        )

        real_forward, real_state = _make_forward(
            real_fn_callable, include_keys, exclude_keys
        )

        def real_backward(*grads):
            if real_state["inputs"] is None or real_state["outputs"] is None:
                raise RuntimeError(
                    "invoke_leaf_function backward expects inputs/outputs to be set in forward."
                )
            return autograd_grad_with_gradient_info(
                output_infos=real_state["outputs"],
                input_infos=real_state["inputs"],
                grad_outputs=grads,
                allow_unused=True,
            )

        input_infos_for_fake = tuple(
            GradientInfo(
                edge=None,  # type: ignore[arg-type]
                size=arg.size(),
                stride=arg.stride(),
                dtype=arg.dtype,
                device=arg.device,
            )
            if isinstance(arg, torch.Tensor) and arg.requires_grad
            else None
            for arg in flat_args
        )

        def fake_backward(*grads):
            return tuple(
                torch.empty_strided(
                    info.size, info.stride, dtype=info.dtype, device=info.device
                )
                if info is not None
                else None
                for info in input_infos_for_fake
            )

        new_real_fn_callable = _LeafCallable(real_forward)

        with torch._C._AutoDispatchBelowAutograd():
            fw_outputs = invoke_leaf_function(
                new_real_fn_callable,
                fake_fn_callable,
                input_spec,
                mutated_arg_indices,
                *flat_args,
                requires_grad_indices=requires_grad_indices,
            )

        hook_real = getattr(real_fn_callable, "_leaf_hook_real_fn", None)
        hook_fake = getattr(real_fn_callable, "_leaf_hook_fake_fn", None)
        if hook_real is not None:
            assert hook_fake is not None  # noqa: S101
            hook_captured_out_spec: list[pytree.TreeSpec | None] = [None]
            wrapped_hook_real, wrapped_hook_fake = make_leaf_function_wrappers(
                hook_real, hook_fake, hook_captured_out_spec
            )
            hook_real_callable = _LeafCallable(wrapped_hook_real)
            hook_fake_callable = _LeafCallable(wrapped_hook_fake)

            grad_tensors = [
                arg
                for arg in flat_args
                if isinstance(arg, torch.Tensor) and arg.requires_grad
            ]
            if grad_tensors:

                @torch._dynamo.disable
                def _multi_grad_callback(
                    grads: Sequence[torch.Tensor],
                ) -> None:
                    _, hook_spec = pytree.tree_flatten((tuple(grads), {}))
                    invoke_leaf_function(
                        hook_real_callable,
                        hook_fake_callable,
                        hook_spec,
                        "",
                        *grads,
                    )

                torch.autograd.graph.register_multi_grad_hook(
                    grad_tensors, _multi_grad_callback
                )

        ctx.real_backward = real_backward
        ctx.fake_backward = fake_backward

        return fw_outputs