def _jvp_with_argnums(
    func: Callable[..., Any],
    primals: Any,
    tangents: Any,
    argnums: argnums_t | None,
    *,
    strict: bool = False,
    has_aux: bool,
) -> tuple[Any, Any] | tuple[Any, Any, Any]:
    # This is the same function as jvp but also accepts an argnums argument
    # Most args are the same as jvp except for the added argument
    # argnums (int or tuple[int, ...]): Optional, specifies the argument(s) to compute gradients with respect to.
    #         If None, computes the gradients with respect to all inputs (used for jvp). Default: None
    # Because of this, tangents must be of length argnums and matches up to the corresponding primal whose index is
    # given by argnums
    #
    # WARN: Users should NOT call this function directly and should just be calling jvp.
    # It is only separated so that inputs passed to jacfwd but not differentiated get the correct wrappers.
    #
    # NOTE: All error messages are produced as if jvp was being called, even if this was called by jacfwd
    #
    # Returns the same two elements as :func:`jvp` but the returned tuple, ``jvp_out``, only has JVPs with respect to
    # the primals given by argnums
    if not isinstance(primals, tuple):
        raise RuntimeError(
            f"{jvp_str}: Expected primals to be a tuple. "
            f"E.g. it should be valid to call f(*primals)."
        )
    diff_args = primals if argnums is None else _slice_argnums(primals, argnums)
    flat_primals, primals_spec = tree_flatten(diff_args)
    flat_tangents, tangents_spec = tree_flatten(tangents)
    if primals_spec != tangents_spec:
        raise RuntimeError(
            f"{jvp_str}: Expected primals and tangents to have the same python "
            f"structure. For example, if primals is a tuple of 3 tensors, "
            f"tangents also must be. Got primals with structure {primals_spec} "
            f"and tangents with structure {tangents_spec}"
        )
    assert_non_empty_list_of_tensors(flat_primals, jvp_str, "primals")
    assert_non_empty_list_of_tensors(flat_tangents, jvp_str, "tangents")

    global JVP_NESTING

    with jvp_increment_nesting() as level:
        with fwAD._set_fwd_grad_enabled(True):
            ctx = fwAD.dual_level if JVP_NESTING == 1 else contextlib.nullcontext
            with ctx():
                flat_duals = tuple(
                    fwAD.make_dual(p, t) for p, t in zip(flat_primals, flat_tangents)
                )
                duals = tree_unflatten(flat_duals, primals_spec)
                if argnums is not None:
                    primals = _wrap_all_tensors(primals, level)
                    duals = _replace_args(primals, duals, argnums)
                result_duals = func(*duals)
                aux: Any = None
                if has_aux:
                    if not (isinstance(result_duals, tuple) and len(result_duals) == 2):
                        raise RuntimeError(
                            f"{jvp_str}: output of function f should be a tuple: (output, aux) "
                            "if has_aux is True"
                        )
                    result_duals, aux = result_duals
                    aux = _undo_create_differentiable(aux, level)

                result_duals, spec = tree_flatten(result_duals)
                assert_non_empty_tensor_output(result_duals, jvp_str)

                primals_out, tangents_out = zip(
                    *[safe_unpack_dual(dual, strict) for dual in result_duals]
                )
                primals_out = tree_map(
                    partial(_undo_create_differentiable, level=level), primals_out
                )
                tangents_out = tree_map(
                    partial(_undo_create_differentiable, level=level), tangents_out
                )

                primals_out_unflatten = tree_unflatten(primals_out, spec)
                tangents_out_unflatten = tree_unflatten(tangents_out, spec)
                if has_aux:
                    return primals_out_unflatten, tangents_out_unflatten, aux  # type: ignore[possibly-unbound]

                return primals_out_unflatten, tangents_out_unflatten