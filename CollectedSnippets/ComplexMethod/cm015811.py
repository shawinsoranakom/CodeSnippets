def test_comprehensive(self, device, dtype, op):
        device_type = torch.device(device).type

        if device_type not in (GPU_TYPE, "cpu"):
            raise AssertionError(f"Unexpected device_type: {device_type}")

        torch._dynamo.reset()
        with torch.no_grad():
            # TODO: should we move empty_cache to the common device interface
            if device_type == "cuda":
                torch.cuda.empty_cache()
            elif device == "xpu":
                torch.xpu.empty_cache()
        op_name = op.name
        if op.variant_test_name:
            op_name += f".{op.variant_test_name}"

        # Skip dtype=torch.uint8 for all ops except upsample and interpolate:
        allowed_dtypes = [f16, f32, f64, i32, i64, b8]
        if op_name not in (
            "nn.functional.interpolate.bilinear",
            "nn.functional.interpolate.bicubic",
            "nn.functional.upsample_bilinear",
            "nn.functional.upsample_nearest",
            "fill",
            "full_like",
        ):
            if dtype not in allowed_dtypes:
                raise unittest.SkipTest("Skipped!")

        # with open("test_output.txt", "a") as f:
        #     print(f"CONSIDERING OP {op_name} on {device_type} with {dtype} |
        # {inductor_skips[device_type].get(op_name, set())}", flush=True, file=f)
        #     print(f"CONSIDERING OP {op_name} on {device_type} with {dtype} |
        # {inductor_skips[device_type].get(op_name, set())}", flush=True)
        if dtype in inductor_skips[device_type].get(op_name, set()):
            test_expect = ExpectedTestResult.SKIP
            # with open("test_output.txt", "a") as f:
            #     print(f"SKIPPING OP {op_name} on {device_type}", flush=True, file=f)
            #     print(f"SKIPPING OP {op_name} on {device_type}", flush=True)
        elif (
            device_type == "cpu"
            and IS_LINUX
            and dtype
            in inductor_expected_failures_single_sample[device_type].get(op_name, set())
        ) or dtype in inductor_gradient_expected_failures_single_sample[
            device_type
        ].get(op_name, set()):
            test_expect = ExpectedTestResult.XFAILURE
        else:
            test_expect = ExpectedTestResult.SUCCESS  # noqa: F841

        overridden_kwargs = {}
        overridden_kwargs.update(
            inductor_override_kwargs.get(device_type, {}).get(op_name, {})
        )
        overridden_kwargs.update(
            inductor_override_kwargs.get(device_type, {}).get((op_name, dtype), {})
        )
        func = op.get_op()

        def fn(*args, **kwargs):
            return func(*args, **kwargs)

        requires_grad = (
            op.supports_autograd
            and dtype in op.supported_backward_dtypes(device_type)
            # TODO: OpInfo really ought to error out for this case, but it's
            # not exercised in test_ops_gradients atm.  The problem is not
            # complex32 per-se (which is supported by data movement only ops)
            # but that when we do backwards we expect other ops like add to work
            and dtype != torch.complex32
        )
        samples = op.sample_inputs(device, dtype, requires_grad=requires_grad)
        extra = _inductor_extra_samples(op_name, device, dtype, requires_grad)
        if extra:
            samples = itertools.chain(samples, extra)

        if (
            dtype in inductor_one_sample.get(device_type, {}).get(op_name, {})
        ) and not ALL_SAMPLES:
            if isinstance(samples, (list, tuple)):
                samples = [samples[0]]
            else:
                samples = [next(samples)]

        class HasRngOp(TorchDispatchMode):
            def __init__(self) -> None:
                super().__init__()
                self.has_rng_op = False

            def __torch_dispatch__(self, func, types, args, kwargs=None):
                kwargs = kwargs if kwargs else {}
                if torch.Tag.nondeterministic_seeded in func.tags:
                    self.has_rng_op = True

                return func(*args, **kwargs)

        def do_nopython_and_has_rng(fn, args, kwargs):
            try:
                mode = FakeTensorMode()

                def map_to_fake(e):
                    if isinstance(e, torch.Tensor):
                        return mode.from_tensor(e)
                    else:
                        return e

                args, kwargs = tree_map(map_to_fake, (args, kwargs))
                with HasRngOp() as rng_mode, mode:
                    with enable_python_dispatcher():
                        fn(*args, **kwargs)

            except (DataDependentOutputException, DynamicOutputShapeException):
                return False, rng_mode.has_rng_op

            return True, rng_mode.has_rng_op

        def get_contexts(has_rng_op, args, kwargs):
            if has_rng_op:
                # TODO - enable this, running into errors
                return (
                    # (
                    #     lambda: torch._inductor.config.patch(
                    #         {"fallback_random": True, "implicit_fallbacks": True}
                    #     ),
                    #     {"assert_equal": True},
                    # ),
                    (
                        contextlib.nullcontext,
                        {"assert_equal": False},
                    ),
                )

            ctx = functools.partial(maybe_skip_size_asserts, op)
            if op_name in CUSTOM_ASSERT_EQUALS_FNS:
                assert_equal_fn = CUSTOM_ASSERT_EQUALS_FNS[op_name](args, kwargs)
                return (
                    (
                        ctx,
                        {"assert_equal": assert_equal_fn},
                    ),
                )

            return ((ctx, {}),)

        try:

            def _get_tolerances(dtype):
                _custom_tolerances = {
                    torch.float32: (1.3e-5, 1.5e-5),
                }
                # When we are running opportunistic_fastatomics, we will expect some floating point rounding
                # errors as the order of operation is not guaranteed.
                if dtype in _custom_tolerances:
                    return _custom_tolerances[dtype]
                else:
                    return None, None

            for sample_input in samples:
                args = [sample_input.input] + list(sample_input.args)
                kwargs = sample_input.kwargs
                # UNCOMMENT TO DEBUG SEGFAULTS

                # with open("test_output.txt", "a") as f:
                #     print(f"RUNNING OP {op_name} on {device_type} with {dtype}", flush=True, file=f)
                #     print(f"RUNNING OP {op_name} on {device_type} with {dtype}", flush=True)
                rtol, atol = _get_tolerances(dtype)
                no_python, has_rng_op = do_nopython_and_has_rng(fn, args, kwargs)
                for context_fn, kwarg_overrides in get_contexts(
                    has_rng_op, args, kwargs
                ):
                    with context_fn():
                        # Base kwargs
                        adjusted_kwargs = {
                            "check_lowp": False,
                            "nopython": no_python,
                            "check_has_compiled": no_python,
                            "atol": atol,
                            "rtol": rtol,
                        }

                        # Backend-specific adjustments
                        # Triton
                        if has_triton():
                            adjusted_kwargs.update(
                                copy_to_gpu=False,
                            )
                            if device_type == GPU_TYPE:
                                adjusted_kwargs["reference_in_float"] = False

                        # skip checking gradient on CPU for now
                        if device_type == GPU_TYPE:
                            adjusted_kwargs.update(
                                check_gradient=requires_grad,
                                output_process_fn_grad=sample_input.output_process_fn_grad,
                            )
                        else:
                            adjusted_kwargs["check_gradient"] = False

                        # Update with overridden kwargs and context-specific overrides
                        adjusted_kwargs.update(overridden_kwargs)
                        adjusted_kwargs.update(kwarg_overrides)

                        # Call the appropriate check method based on device type
                        exact_stride = op_name not in inductor_skip_exact_stride
                        # XPU has additional layout optimizations that change strides differently from eager mode.
                        if exact_stride and GPU_TYPE == "xpu":
                            exact_stride = op_name not in inductor_skip_exact_stride_xpu
                        if device_type == GPU_TYPE:
                            self.check_model_gpu(
                                fn,
                                args,
                                kwargs,
                                **adjusted_kwargs,
                                exact_stride=exact_stride,
                            )
                        else:
                            self.check_model(
                                fn,
                                args,
                                kwargs,
                                **adjusted_kwargs,
                                exact_stride=exact_stride,
                            )

        except Exception as e:
            known_failure = False
            if dtype in inductor_should_fail_with_exception[device_type].get(
                op_name, set()
            ):
                failure = inductor_should_fail_with_exception[device_type][op_name][
                    dtype
                ]
                if failure in str(e):
                    known_failure = True
            if not known_failure:
                raise e