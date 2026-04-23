def wrapper_fn(*args: Any) -> Any:
        error_if_complex("jacfwd", args, is_input=True)
        primals = args if argnums is None else _slice_argnums(args, argnums)
        flat_primals, primals_spec = tree_flatten(primals)
        flat_primals_numels = tuple(p.numel() for p in flat_primals)
        flat_basis = _construct_standard_basis_for(flat_primals, flat_primals_numels)
        if flat_basis is None:
            raise AssertionError("flat_basis must not be None")
        basis = tree_unflatten(flat_basis, primals_spec)

        def push_jvp(basis: Any) -> Any:
            output = _jvp_with_argnums(
                func, args, basis, argnums=argnums, has_aux=has_aux
            )
            # output[0] is the output of `func(*args)`
            error_if_complex("jacfwd", output[0], is_input=False)
            if has_aux:
                _, jvp_out, aux = output  # pyrefly: ignore[bad-unpacking]
                return jvp_out, aux
            _, jvp_out = output  # pyrefly: ignore[bad-unpacking]
            return jvp_out

        results = vmap(push_jvp, randomness=randomness)(basis)
        aux: Any = None
        if has_aux:
            results, aux = results
            # aux is in the standard basis format, e.g. NxN matrix
            # We need to fetch the first element as original `func` output
            flat_aux, aux_spec = tree_flatten(aux)
            flat_aux = [value[0] for value in flat_aux]
            aux = tree_unflatten(flat_aux, aux_spec)

        jac_outs, spec = tree_flatten(results)
        # Most probably below output check can never raise an error
        # as jvp should test the output before
        # assert_non_empty_output(jac_outs, 'jacfwd(f, ...)(*args)')

        jac_outs_ins = tuple(
            tuple(
                safe_unflatten(jac_out_in, -1, primal.shape)
                for primal, jac_out_in in zip(
                    flat_primals,
                    jac_out.movedim(0, -1).split(flat_primals_numels, dim=-1),
                )
            )
            for jac_out in jac_outs
        )
        jac_outs_ins = tuple(
            tree_unflatten(jac_ins, primals_spec) for jac_ins in jac_outs_ins
        )

        if isinstance(argnums, int):
            jac_outs_ins = tuple(jac_ins[0] for jac_ins in jac_outs_ins)
        if has_aux:
            return tree_unflatten(jac_outs_ins, spec), aux  # type: ignore[possibly-unbound]
        return tree_unflatten(jac_outs_ins, spec)