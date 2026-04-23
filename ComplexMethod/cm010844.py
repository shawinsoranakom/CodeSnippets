def inner_fn(
        primals: list[FxValue], tangents: list[FxValue]
    ) -> tuple[
        tuple[list[FxValue], list[Tensor | None]],
        tuple[list[AOTOutput], list[AOTOutput | None]],
    ]:
        outs_descs = None
        if primals_descs is None:
            outs, tangent_mask = fn(*primals)
            if pytree.tree_any(lambda x: isinstance(x, AOTOutput), tangent_mask):
                raise AssertionError(
                    "tangent_mask should not contain AOTOutput instances"
                )
        else:
            (outs, tangent_mask), (outs_descs, _) = call_and_expect_output_descs(
                fn,
                primals,  # type: ignore[arg-type]
            )
        mode = get_proxy_mode()
        if mode is None:
            raise AssertionError("Expected non-None proxy mode")
        for node in mode.tracer.graph.nodes:
            if _is_tangent(node):
                node.meta["partitioner_tag"] = "is_backward"
            else:
                node.meta["partitioner_tag"] = "is_forward"

        # TODO: I think this hook can also be eliminated now
        if joint_fn_handle and joint_fn_handle.post_forward:
            joint_fn_handle.post_forward(primals)

        if len(tangent_mask) != len(outs):
            raise AssertionError(
                f"tangent_mask length ({len(tangent_mask)}) != outs length ({len(outs)})"
            )
        outs_to_grad = [
            o for needs_tangent, o in zip(tangent_mask, outs) if needs_tangent
        ]
        if len(outs_to_grad) != len(tangents):
            raise AssertionError(
                f"outs_to_grad length ({len(outs_to_grad)}) != tangents length ({len(tangents)})"
            )

        # Get the inputs that need gradients
        grad_primals: list[torch.Tensor] = []
        inputs_needs_grads = []
        # Note that we're not using primals here,
        # being carefully not to pass any mutated inputs into autograd.grad()
        for p in primals:
            if isinstance(p, Tensor) and p.requires_grad:
                inputs_needs_grads.append(True)
                if not isinstance(p, torch.Tensor):  # Help mypy understand the type
                    raise AssertionError(f"expected Tensor, got {type(p)}")
                grad_primals.append(p)
            else:
                inputs_needs_grads.append(False)

        # Get the outputs that need gradients
        needed_outs: list[Tensor] = []
        needed_tangents: list[Tensor] = []
        for out, tangent in zip(outs_to_grad, tangents):
            if isinstance(out, Tensor) and out.requires_grad:
                # A bit sketchy, but fixes e.g. test_aot_autograd_exhaustive_matmul_cpu_float32
                # The issue is that we are sensitive to decomps that don't accurately maintain
                # their output's _base.shape compared to eager mode, and this helps mitigate a bit.
                # The guard_or_true also sketchy; if unbacked
                # symints are involved, we're just going to assume that the
                # decomps setup the base shape correctly

                # Return out if the result of out.shape==tangent.shape is unknown or known to be true.
                # otherwise if its a known false return out.view(tangent.shape).
                # tangent should also be a tensor since it corresponds to a tensor output
                if not isinstance(tangent, torch.Tensor):
                    raise AssertionError(
                        f"Expected tensor tangent, got {type(tangent)}"
                    )
                needed_outs.append(
                    out
                    if guard_or_true(sym_eq(out.shape, tangent.shape))
                    else out.view(tangent.shape)
                )
                needed_tangents.append(tangent)

        setup_stacktrace_preservation_hooks(
            [out.grad_fn for out in needed_outs if out.grad_fn is not None]
        )

        if config.functionalize_rng_ops:
            PhiloxStateTracker.mark_beginning_of_backward()
        backward_out: tuple[Tensor, ...] = ()
        # Call the backwards pass
        if grad_primals:
            functional_tensor_mode = torch.utils._python_dispatch._detect_infra_mode(
                torch._C._TorchDispatchModeKey.FUNCTIONAL
            )
            if functional_tensor_mode is not None:
                # Side-Effect Tokens:
                # We want to have independent chains of tokens for forward and backward.
                # functional_tensor_mode._tokens is used by both.
                # We memoize the result tokens of forward in functional_tensor_mode._tokens_forward_output,
                # to return them as joint graph outputs.
                # We clean functional_tensor_mode._tokens before backward, to prevent reuse of forward tokens in backward.
                # Joint graph tracing allows tokens discovery,
                # So all the tokens in backward will be created and added as a graph inputs during tracing.
                functional_tensor_mode._tokens_forward_output = (
                    functional_tensor_mode._tokens
                )
                functional_tensor_mode._tokens = {}  # pyrefly: ignore[implicit-any]

            with (
                set_partitioner_tag_is_backward(),
                fx_traceback.preserve_node_meta(),
                ExitStack() as stack,
            ):
                backward_pass_autocast = torch._functorch.config.backward_pass_autocast
                if backward_pass_autocast == "same_as_forward":
                    # Use the ambient autocast mode(s)
                    pass
                elif backward_pass_autocast == "off":
                    stack.enter_context(disable_autocast())
                else:
                    # Disable autocast, then enable anything in `backward_pass_autocast`.
                    stack.enter_context(disable_autocast())
                    if not isinstance(backward_pass_autocast, list):
                        raise AssertionError(
                            f"expected backward_pass_autocast to be a list, got {type(backward_pass_autocast)}"
                        )
                    for kwargs in backward_pass_autocast:
                        if not isinstance(kwargs, dict):
                            raise AssertionError(
                                f"expected kwargs to be a dict, got {type(kwargs)}"
                            )
                        stack.enter_context(torch.amp.autocast(**kwargs))

                # for full graph export, we always export a joint graph where we assume no tangents are needed.
                if aot_config.no_tangents:
                    if not (
                        len(needed_tangents) == 1 and needed_tangents[0].numel() == 1
                    ):
                        raise AssertionError(
                            f"expected single scalar tangent for no_tangents mode, got {len(needed_tangents)} tangents"
                        )
                    backward_out = torch.autograd.grad(
                        needed_outs,
                        grad_primals,
                        allow_unused=True,
                    )
                else:
                    backward_out = torch.autograd.grad(
                        needed_outs,
                        grad_primals,
                        grad_outputs=needed_tangents,
                        allow_unused=True,
                    )
        backward_out_iter = iter(backward_out)
        final_outs = (
            outs,
            [next(backward_out_iter) if i else None for i in inputs_needs_grads],
        )
        if primals_descs is None:
            return final_outs  # type: ignore[return-value]
        if outs_descs is None:
            raise AssertionError("outs_descs must not be None")
        # pyrefly: ignore[bad-return]
        return final_outs, (
            outs_descs,
            [
                # TODO: ideally we do know this is DifferentiableAOTInput
                # but this is quite an involved refactor
                GradAOTOutput(desc) if i else None  # type: ignore[arg-type]
                for i, desc in zip(inputs_needs_grads, primals_descs)
            ],
        )