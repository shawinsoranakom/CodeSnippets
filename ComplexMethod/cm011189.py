def _maybe_run_and_benchmark_fallback_kernel(  # type: ignore[no-untyped-def]
        cls,
        func,
        args,
        kwargs,
        orig_not_implemented_exception,
    ):
        """
        Runs and benchmarks a fallback kernel for a given function.

        Args:
            func (Callable): The function to benchmark.
            args (Tuple): The arguments to pass to the function.
            kwargs (Dict[str, Any]): The keyword arguments to pass to the function.
            orig_not_implemented_exception (Exception): The original exception to raise if the fallback kernel
                is not implemented.

        Returns:
            Tuple[Any, float]: A tuple containing the result of the function and
                the mean operation time in milliseconds.
        """
        # these should all be supported, just to be safe
        # avoid fallback for operators which inplace modify metadata
        # because the input fake tensors would be umodified
        if torch.Tag.inplace_view in func.tags:  # type: ignore[attr-defined]
            raise orig_not_implemented_exception

        inp_impls = {}
        flat_args, args_spec = pytree.tree_flatten((args, kwargs))
        # Don't use in_kernel_invocation_manager(fake_mode) as we want to do
        # REAL compute (not with meta device)
        with no_dispatch():

            def to_real_tensor(e):  # type: ignore[no-untyped-def]
                if cls.fake_mode.is_our_fake(e):
                    if e.dtype in _FLOAT_TYPES:
                        out = torch.rand_like(e, device=e.fake_device)
                    else:
                        out = torch.ones_like(e, device=e.fake_device)
                    if e.is_sparse:
                        out._coalesced_(e.is_coalesced())
                    inp_impls[id(out)] = e
                    return out
                return e

            flat_args = [to_real_tensor(a) for a in flat_args]
            args, kwargs = pytree.tree_unflatten(flat_args, args_spec)
            r = func(*args, **kwargs)
            warmup_iters, actual_iters = 2, 3
            for _ in range(warmup_iters):
                func(*args, **kwargs)
            start_event = torch.cuda.Event(enable_timing=True)
            end_event = torch.cuda.Event(enable_timing=True)
            start_event.record(torch.cuda.current_stream())
            for _ in range(actual_iters):
                func(*args, **kwargs)
            end_event.record(torch.cuda.current_stream())
            torch.cuda.synchronize()
            cuda_time = start_event.elapsed_time(end_event)
            mean_op_time = cuda_time / actual_iters

        storages = set()

        for e in flat_args:
            if isinstance(e, torch.Tensor):
                if not e.is_sparse:
                    storages.add(e._typed_storage()._cdata)

        # TODO: also check metadata change on inputs
        # proper aliasing/metadata relationship between outputs and inputs will
        # not be set up, bc of conversion to device, unless we can reuse an
        # input impl

        def map_out(e):  # type: ignore[no-untyped-def]
            if id(e) not in inp_impls and (
                isinstance(e, torch.Tensor)
                and not e.is_sparse
                and e._typed_storage()._cdata in storages
            ):
                raise orig_not_implemented_exception

            if isinstance(e, torch.Tensor):
                if id(e) in inp_impls:
                    return inp_impls[id(e)]
                else:
                    return cls.fake_mode.fake_tensor_converter.from_real_tensor(
                        cls.fake_mode, e
                    )
            else:
                return e

        return (pytree.tree_map(map_out, r), mean_op_time)