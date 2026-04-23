def run_test_output_match(
    test_suite: unittest.TestCase,
    device: str,
    dtype: torch.dtype,
    op: opinfo_core.OpInfo,
    function_executor: Callable,
    tested_op_mapping: dict[
        str,
        ops_test_data.TorchLibOpInfo,
    ],
):
    """Base test method for testing each opset, used by instantiate_device_type_tests.

    Args:
        test_suite: The test class instance.
        device: The PyTorch device. instantiate_device_type_tests provides this.
        dtype: The PyTorch dtype. instantiate_device_type_tests provides this.
        op: The OpInfo instance. instantiate_device_type_tests provides this.
        function_executor: The function executor. This is a function that takes
            a function and its arguments and returns the output of the function.
        tested_op_mapping: The mapping of op name to the tested op.
    """
    samples = op.sample_inputs(
        device,
        dtype,
        requires_grad=False,
    )

    torchlib_op_info = tested_op_mapping[op.name]
    # Obtain the input_wrangler that manipulates the OpInfo inputs
    # to match the aten operator signature
    # An example is nn.functional.upsample_nearest2d, which has a different signature
    # than the aten operator upsample_nearest2d
    onnx_function = torchlib_op_info.op
    input_wrangler = torchlib_op_info.input_wrangler
    if (
        not ops_test_common.dtype_op_schema_compatible(
            dtype, onnx_function.op_signature
        )
        and dtype not in COMPLEX_TYPES
    ):
        test_suite.skipTest(
            f"dtype '{dtype}' is not supported by the op '{op.name}'. "
            f"Type constraints: {onnx_function.op_signature.params}"
        )

    # Obtain the tolerance for the op
    rtol, atol = torchlib_op_info.get_tolerance(dtype)
    for i, cpu_sample in enumerate(samples):
        inputs = (cpu_sample.input, *cpu_sample.args)
        # Provide the repr to subtest because tensors are not serializable in parallel test runs
        with test_suite.subTest(
            sample_num=i,
            inputs=repr(
                [
                    f"Tensor<{inp.shape}, dtype={inp.dtype}>"
                    if isinstance(inp, torch.Tensor)
                    else inp
                    for inp in inputs
                ]
            ),
            kwargs=repr(cpu_sample.kwargs),
        ):
            try:
                device_type = cpu_sample.args[0].device.type
            except (AttributeError, IndexError):
                device_type = "cpu"
            test_behavior, reason = _should_skip_xfail_test_sample(
                op.name, cpu_sample, dtype, device_type
            )

            with ops_test_common.normal_xfail_skip_test_behaviors(
                test_behavior, reason
            ):
                input_onnx = [
                    ops_test_common.convert_tensor_to_numpy(x) for x in inputs
                ]
                kwargs_onnx = ops_test_common.convert_kwargs_for_onnx(cpu_sample.kwargs)
                if input_wrangler:
                    input_onnx, kwargs_onnx = input_wrangler(input_onnx, kwargs_onnx)
                torch_output = op(*inputs, **cpu_sample.kwargs)

                if isinstance(torch_output, torch.Tensor) and torch.is_complex(
                    torch_output
                ):
                    torch_output = torch.view_as_real(torch_output.resolve_conj())

                reference_torch_outputs, _ = pytree.tree_flatten(torch_output)
                if (
                    op.name.startswith("split")
                    or op.name.startswith("chunk")
                    or op.name.startswith("unbind")
                    or op.name
                    in {
                        "atleast_1d_Sequence",
                        "atleast_2d_Sequence",
                        "atleast_3d_Sequence",
                    }
                ):
                    # Hack for handling split, chunk and unbind which relies on SplitToSequence op.
                    # Split returns a Sequence that should be treats as a single
                    # value. So we wrap it into a tuple.
                    # TODO(justinchuby): Find a more general solution
                    reference_torch_outputs = [reference_torch_outputs]

                test_name = test_suite.id()
                function_output, model_proto = function_executor(
                    test_name,
                    reference_torch_outputs,
                    opset_version=torchlib_op_info.opset_introduced,
                )(onnx_function, input_onnx, kwargs_onnx)
                # Finally we re-flatten everything
                # TODO: add pytree structure comparison.
                flattened_torch_outputs, _ = pytree.tree_flatten(torch_output)
                flattened_function_outputs, _ = pytree.tree_flatten(function_output)

                if not flattened_torch_outputs:
                    raise AssertionError("flattened_torch_outputs is empty")
                if len(flattened_torch_outputs) != len(flattened_function_outputs):
                    raise AssertionError(
                        f"Expected {len(flattened_torch_outputs)} outputs, "
                        f"got {len(flattened_function_outputs)}"
                    )

                for j, (torch_output, function_output) in enumerate(
                    zip(flattened_torch_outputs, flattened_function_outputs)
                ):
                    actual = torch.tensor(function_output)
                    expected = (
                        torch_output
                        if isinstance(torch_output, torch.Tensor)
                        else torch.tensor(torch_output)
                    )

                    if (
                        op.name in ops_test_data.NONDETERMINISTIC_OPS
                        or j in ops_test_data.COMPARE_SHAPE_ONLY_OPS[op.name]
                    ):
                        # Check shape and dtype only for ops that are known to be
                        # nondeterministic
                        test_suite.assertEqual(actual.shape, expected.shape)
                        test_suite.assertEqual(actual.dtype, expected.dtype)
                        continue

                    # Use torch.testing as opposed to np.testing to ensure dtypes and shapes match
                    try:
                        torch.testing.assert_close(
                            actual,
                            expected,
                            rtol=rtol,
                            atol=atol,
                            equal_nan=True,
                            check_device=False,
                        )
                    except AssertionError as e:
                        if (
                            os.environ.get("CREATE_REPRODUCTION_REPORT") == "1"
                            and test_behavior is None
                        ):
                            error_reproduction.create_mismatch_report(
                                test_name,
                                i,
                                model_proto,
                                inputs,
                                cpu_sample.kwargs,
                                actual,
                                expected,
                                e,
                                __file__,
                            )
                        if len(flattened_torch_outputs) > 1:
                            raise AssertionError(f"Output {j} mismatch") from e
                        raise