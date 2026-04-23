def wrapped(*primals):
        _args = list(flat_args)
        for num, arg in zip(diff_argnums, primals):
            _args[num] = arg
        _args = tree_unflatten(_args, args_spec)
        result = f(*_args, **kwargs)
        if output_process_fn_grad is not None:
            result = output_process_fn_grad(result)
        if isinstance(result, tuple):
            # TODO We should check that the integer outputs also agree
            result = tuple(
                r
                for r in result
                if isinstance(r, Tensor) and (r.is_floating_point() or r.is_complex())
            )
            if len(result) <= 0:
                raise AssertionError("expected result to be non-empty")
        return result