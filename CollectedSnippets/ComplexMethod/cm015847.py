def check_model(
    self: TestCase,
    model,
    example_inputs,
    kwargs=None,
    *,
    atol=None,
    rtol=None,
    grad_atol=None,
    grad_rtol=None,
    check_lowp=True,
    exact_dtype=True,
    nopython=True,
    copy_to_gpu=True,
    reference_in_float=True,
    assert_equal=True,
    check_gradient=False,
    check_has_compiled=True,
    output_process_fn_grad=lambda x: x,
    # TODO: enable this for all tests
    exact_stride=False,
):
    kwargs = kwargs or {}
    torch._dynamo.reset()

    ref_inputs = [clone_preserve_strides_offset(x) for x in example_inputs]
    ref_kwargs = kwargs
    has_lowp_args = False

    if reference_in_float and exact_dtype:
        # Store expected dtypes so we can check actual result gives the correct types
        torch.manual_seed(0)
        try:
            eager_result = model(*ref_inputs, **ref_kwargs)
        except RuntimeError:
            # Eager model may fail if the dtype is not supported
            eager_result = None

        ref_inputs = [clone_preserve_strides_offset(x) for x in example_inputs]
        expect_dtypes = [
            x.dtype if isinstance(x, torch.Tensor) else None
            for x in pytree.tree_leaves(eager_result)
        ]
        del eager_result

    ref_model = model
    if reference_in_float:
        # check_lowp is ignored here, it's kept just to be able to call `common` with extra arg
        def upcast_fn(x):
            nonlocal has_lowp_args
            if isinstance(x, torch.Tensor) and (
                x.dtype == torch.float16 or x.dtype == torch.bfloat16
            ):
                has_lowp_args = True
                # Preserve strides when casting
                result = torch.empty_strided(
                    x.size(), x.stride(), device=x.device, dtype=torch.float
                )
                result.copy_(x)
                return result
            else:
                return x

        # We previously call upcast_fn on example_inputs. It's incorrect
        # if example_inputs is already fp32 and get inplace updated in the model.
        # Call on the cloned tensors instead
        ref_inputs = list(map(upcast_fn, ref_inputs))
        ref_kwargs = {k: upcast_fn(v) for k, v in kwargs.items()}
        if has_lowp_args and hasattr(model, "to"):
            ref_model = copy.deepcopy(model).to(torch.float)

    torch.manual_seed(0)

    correct = ref_model(*ref_inputs, **ref_kwargs)

    torch._inductor.metrics.reset()

    called = False

    def compile_fx_wrapper(model_, example_inputs_):
        nonlocal called
        called = True
        return compile_fx(model_, example_inputs_)

    def run(*ex, **kwargs):
        return model(*ex, **kwargs)

    run = torch.compile(run, backend=compile_fx_wrapper, fullgraph=nopython)

    torch.manual_seed(0)
    actual = run(*example_inputs, **kwargs)
    # if not called:
    #     exp = torch._dynamo.explain(run)(*example_inputs)
    #     print("Explain:", exp[0])
    #     for graph in exp[2]:
    #         print("Graph", graph)
    if check_has_compiled:
        if not called:
            raise AssertionError("Ran graph without calling compile_fx")
    if type(actual) is not type(correct):
        raise AssertionError(f"Expected type {type(correct)}, got {type(actual)}")
    if isinstance(actual, (tuple, list)):
        if len(actual) != len(correct):
            raise AssertionError(f"Expected length {len(correct)}, got {len(actual)}")
        if not all(
            type(actual_item) is type(correct_item)
            for actual_item, correct_item in zip(actual, correct)
        ):
            raise AssertionError(
                f"Item type mismatch: expected types {[type(c) for c in correct]}, "
                f"got {[type(a) for a in actual]}"
            )

    correct_flat, correct_spec = tree_flatten(correct)
    actual_flat = pytree.tree_leaves(actual)

    def to_dtype_preserve_strides(src, dtype):
        if any(s == 0 for s in src.stride()):
            return src.to(dtype)
        # Preserve strides when casting.
        result = torch.empty_strided(
            src.size(), src.stride(), device=src.device, dtype=dtype
        )
        result.copy_(src)
        return result

    def reference_to_expect(actual_flat, correct_flat):
        return tuple(
            (
                to_dtype_preserve_strides(y, x.dtype)
                if isinstance(y, torch.Tensor) and y.dtype.is_floating_point
                else y
            )
            for x, y in zip(actual_flat, correct_flat)
        )

    if reference_in_float and exact_dtype:
        for expect_dtype, actual_result in zip(expect_dtypes, actual_flat):
            if expect_dtype is not None:
                if actual_result.dtype != expect_dtype:
                    raise AssertionError(
                        f"dtype mismatch, expected {expect_dtype} but got {actual_result.dtype}"
                    )

    if reference_in_float:
        correct_flat = reference_to_expect(actual_flat, correct_flat)
        correct = tree_unflatten(correct_flat, correct_spec)

    def has_zero_dim(x):
        if not isinstance(x, tuple):
            x = (x,)
        return any(isinstance(t, torch.Tensor) and 0 in t.size() for t in x)

    # Allow assert_equal to be a custom function, instead of True or False, for
    # cases where differences may not indicate incorrectness.
    if assert_equal:
        if callable(assert_equal):

            def custom_assert_with_self(*args, **kwargs):
                assert_equal(self, *args, **kwargs)

            assert_equal_fn = custom_assert_with_self
        else:
            assert_equal_fn = self.assertEqual

        check_exact_stride = exact_stride and not has_zero_dim(correct)
        assert_equal_fn(
            actual,
            correct,
            atol=atol,
            rtol=rtol,
            equal_nan=True,
            exact_dtype=exact_dtype,
            exact_stride=check_exact_stride,
        )
        # In case of input mutations, check that inputs are the same
        # (This never uses a custom assert_equal fn.)
        self.assertEqual(
            ref_inputs,
            example_inputs,
            atol=atol,
            rtol=rtol,
            equal_nan=True,
            # our testing sometimes uses higher precision inputs for the reference
            exact_dtype=False,
            exact_stride=exact_stride,
        )
    else:
        for correct_val, actual_val in zip(correct_flat, actual_flat):
            if isinstance(correct_val, torch.Tensor):
                if correct_val.device != actual_val.device:
                    raise AssertionError(
                        f"Expected device {correct_val.device}, got {actual_val.device}"
                    )
                if correct_val.size() != actual_val.size():
                    raise AssertionError(
                        f"Expected size {correct_val.size()}, got {actual_val.size()}"
                    )
                strides_equal, _ = torch._prims_common.check_significant_strides(
                    correct_val, actual_val
                )
                if not strides_equal:
                    raise AssertionError(
                        f"Significant strides mismatch: expected {correct_val.stride()}, "
                        f"got {actual_val.stride()}"
                    )
                if correct_val.layout != actual_val.layout:
                    raise AssertionError(
                        f"Expected layout {correct_val.layout}, got {actual_val.layout}"
                    )
                if exact_dtype:
                    if correct_val.dtype != actual_val.dtype:
                        raise AssertionError(
                            f"Expected dtype {correct_val.dtype}, got {actual_val.dtype}"
                        )
                check_exact_stride = exact_stride and not has_zero_dim(correct_val)
                if check_exact_stride:
                    if correct_val.stride() != actual_val.stride():
                        raise AssertionError(
                            f"Expected stride {correct_val.stride()}, got {actual_val.stride()}"
                        )

    if check_gradient:
        actual = output_process_fn_grad(actual)
        correct = output_process_fn_grad(correct)
        actual_flat = pytree.tree_leaves(actual)
        correct_flat = pytree.tree_leaves(correct)

        # generate random unit norm gradients
        grads = [
            torch.randn_like(r)
            for r in correct_flat
            if isinstance(r, torch.Tensor) and r.requires_grad
        ]
        for g in grads:
            g /= g.norm()

        correct_grad = compute_grads(ref_inputs, ref_kwargs, correct, grads)
        all_none_grads = all(x is None for x in correct_grad)
        tensor_args = [
            x
            for x in pytree.tree_flatten(example_inputs)[0]
            if isinstance(x, torch.Tensor)
        ]
        any_non_leaves = any(x.grad_fn is not None for x in tensor_args)
        if all_none_grads and any_non_leaves:
            # See Note [Detaching inputs that never need gradients]
            # There are a handful of ops that can return None gradients, into of zero gradients.
            # If all inputs to an AOTAutograd graph are supposed to get None gradients,
            # AOTAutograd will end up forcing all of the outputs of the forward to not require grad.
            # There's no easy fix to this (see the note above), although one option is to
            # force any derivative formulas in core to return tensors of zeros instead of None.
            flat_results = pytree.tree_leaves(actual)
            results_that_require_grad = [
                x
                for x in flat_results
                if isinstance(x, torch.Tensor) and x.requires_grad
            ]
            self.assertEqual(len(results_that_require_grad), 0)
        else:
            actual_grad = compute_grads(example_inputs, kwargs, actual, grads)

            if reference_in_float:
                expect_grad = reference_to_expect(actual_grad, correct_grad)
            else:
                expect_grad = correct_grad

            for actual_g, expect_g in zip(actual_grad, expect_grad):
                check_exact_stride = exact_stride and not has_zero_dim(expect_g)
                self.assertEqual(
                    actual_g,
                    expect_g,
                    atol=grad_atol or atol,
                    rtol=grad_rtol or rtol,
                    equal_nan=True,
                    exact_dtype=exact_dtype,
                    exact_stride=check_exact_stride,
                )

    torch._dynamo.reset()