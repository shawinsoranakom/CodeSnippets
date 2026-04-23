def aot_autograd_check(
        func,
        args,
        kwargs,
        dynamic,
        assert_raises_regex_fn=assert_raises_regex,
        assert_equals_fn=torch.testing.assert_close,
        check_gradients=True,
        try_check_data_specialization=False,
        skip_correctness_check=False,
        disable_functionalization=False):
    """Compares func(*args, **kwargs) in eager-mode to under AOTAutograd.

    Compares outputs and (if check_gradients=True) gradients produced by
    AOTAutograd against eager-mode PyTorch.

    We assume that func(*args, **kwargs) succeeds in eager-mode PyTorch.

    """
    flat_args, args_spec = pytree.tree_flatten((args, kwargs))
    args = [arg for arg in flat_args if isinstance(arg, torch.Tensor)]

    # We construct a new function that only accepts Tensors as inputs
    def func_no_tensors(args):
        reconstructed_flat_args = []
        args = iter(args)
        for v in flat_args:
            if isinstance(v, torch.Tensor):
                reconstructed_flat_args.append(next(args))
            else:
                reconstructed_flat_args.append(v)

        c_args, c_kwargs = pytree.tree_unflatten(reconstructed_flat_args, args_spec)
        return func(*c_args, **c_kwargs)

    # cannot use the min cut partitioner without functionalization
    if disable_functionalization:
        compiled_f = compiled_function(
            func_no_tensors,
            nop,
            nop,
            dynamic=dynamic,
            partition_fn=default_partition,
            keep_inference_input_mutations=True,
            disable_functionalization=True
        )
    else:
        compiled_f = compiled_function(
            func_no_tensors,
            nop,
            nop,
            dynamic=dynamic,
            partition_fn=min_cut_rematerialization_partition,
            keep_inference_input_mutations=True,
            disable_functionalization=False
        )

    out = wrapper_set_seed(func_no_tensors, args)
    if check_gradients == "auto":
        any_tensor_requires_grad = pytree.tree_any_only(torch.Tensor, lambda x: x.requires_grad, args)
        any_output_requires_grad = pytree.tree_any_only(torch.Tensor, lambda x: x.requires_grad, out)
        check_gradients = any_tensor_requires_grad and any_output_requires_grad
    if not check_gradients:
        compiled_out = wrapper_set_seed(compiled_f, args)
        if not skip_correctness_check:
            assert_equals_fn(compiled_out, out, msg=outputs_msg)
        return
    _test_aot_autograd_forwards_backwards_helper(
        func_no_tensors, compiled_f, args, assert_raises_regex_fn, assert_equals_fn,
        try_check_data_specialization, skip_correctness_check)