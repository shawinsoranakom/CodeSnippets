def _vjp_with_argnums(
    func: Callable[..., Any],
    *primals: Any,
    argnums: argnums_t | None = None,
    has_aux: bool = False,
) -> tuple[Any, Callable[..., Any]] | tuple[Any, Callable[..., Any], Any]:
    # This is the same function as vjp but also accepts an argnums argument
    # All args are the same as vjp except for the added argument
    # argnums (int or tuple[int,...] | None): Optional, specifies the argument(s) to compute gradients with respect to.
    #         If None, computes the gradients with respect to all inputs (used for vjp). Default: None
    #
    # WARN: Users should NOT call this function directly and should just be calling vjp.
    # It is only separated so that inputs passed to jacrev but not differentiated get the correct wrappers.
    #
    # NOTE: All error messages are produced as if vjp was being called, even if this was called by jacrev
    #
    # Returns the same two elements as :func:`vjp` but the function returned, vjp_fn, returns a tuple of VJPs
    # for only the primal elements given by argnums.
    with grad_increment_nesting() as level:
        # See NOTE [grad and vjp interaction with no_grad]
        with torch.enable_grad():
            primals = _wrap_all_tensors(primals, level)
            if argnums is None:
                diff_primals = _create_differentiable(primals, level)
            else:
                diff_primals = _slice_argnums(primals, argnums, as_tuple=False)
                tree_map_(partial(_create_differentiable, level=level), diff_primals)
            primals_out = func(*primals)

            aux: Any = None
            if has_aux:
                if not (isinstance(primals_out, tuple) and len(primals_out) == 2):
                    raise RuntimeError(
                        "vjp(f, *primals): output of function f should be a tuple: (output, aux) "
                        "if has_aux is True"
                    )
                primals_out, aux = primals_out
                aux = _undo_create_differentiable(aux, level)

            flat_primals_out, primals_out_spec = tree_flatten(primals_out)
            assert_non_empty_tensor_output(flat_primals_out, "vjp(f, *primals)")
            flat_diff_primals, primals_spec = tree_flatten(diff_primals)
            results = _undo_create_differentiable(primals_out, level)

            for primal_out in flat_primals_out:
                if not isinstance(primal_out, torch.Tensor):
                    raise AssertionError(
                        f"expected primal_out to be a Tensor, got {type(primal_out)}"
                    )
                if primal_out.is_floating_point() or primal_out.is_complex():
                    continue
                raise RuntimeError(
                    "vjp(f, ...): All outputs of f must be "
                    "floating-point or complex Tensors, got Tensor "
                    f"with dtype {primal_out.dtype}"
                )

        def wrapper(
            cotangents: Any,
            retain_graph: bool = True,
            create_graph: bool | None = None,
        ) -> Any:
            if create_graph is None:
                create_graph = torch.is_grad_enabled()
            flat_cotangents, cotangents_spec = tree_flatten(cotangents)
            if primals_out_spec != cotangents_spec:
                raise RuntimeError(
                    f"Expected pytree structure of cotangents to be the same "
                    f"as pytree structure of outputs to the function. "
                    f"cotangents: {treespec_pprint(cotangents_spec)}, "
                    f"primal output: {treespec_pprint(primals_out_spec)}"
                )
            # This closure runs after grad_increment_nesting exits, so
            # inference_mode may have been restored. Disable it for autograd.
            # Skip under Dynamo — tracing through the generator CM emits
            # spurious _enter_inference_mode nodes.
            ctx = (
                contextlib.nullcontext()
                if torch.compiler.is_compiling()
                else _disable_inference_mode()
            )
            with ctx:
                result = _autograd_grad(
                    flat_primals_out,
                    flat_diff_primals,
                    flat_cotangents,
                    retain_graph=retain_graph,
                    create_graph=create_graph,
                )
            return tree_unflatten(result, primals_spec)

    if has_aux:
        return results, wrapper, aux  # type: ignore[possibly-unbound]
    else:
        return results, wrapper