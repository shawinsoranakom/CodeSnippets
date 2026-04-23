def _test_activation_function(self, X, fn_name, test_configs):
        r"""
            When writing a unit test for the activation function,
            instead of specifying the test routines only applicable to the activation function itself,
            you utilize the _test_activation_function that provides general testing.
            To utilize the helper function, a test config must be provided.
            A test config is a list that contains metadata about the quantized activation
            functions that will be tested and how the tests need to be set up; it allows simpler and
            more concise unit tests to be written by specifying the configurations needed
            and calling the provided helper function _test_activation_function.
            Inside the list, each config (as a dictionary) represents a suite of tests that assert the
            correctness of various quantization functions.
            You can check out the test_qrelu, test_qrelu6, test_qsigmoid, and test_qhardsigmoid for
            how their test configs are specified.
            Here's a list of the fields that can be included in a test config:
            quantized_fn: a list of the quantized functions to be tested
            reference_fn: the original reference function to be called on the
            the dequantized X
            extra_kwargs: the additional keyword arguments
            for each test entry in ops_under_test, it must have at least the fields
            for quantized_fn and reference_fn.
            output_range: the output range the operator will map to. By default, if it is
            no specified, the range will not be controlled and depend on Xmin and Xmax.
            change_zero_point: a boolean flag indicating if the zero point parameter should
            be determined based on torch_type during quantization (see sigmoid/hardsigmoid for
            examples). By default, if it is not specified, change_zero_point is assumed to be
            False and zero point will just take on the default value from X.
            `output_is_observed`: if specified and is True, we'll append extra
             output_scale/output_zero_point keyword argument when calling quantized op
        """
        # Retrieves the default parameters from X.
        X, (scale, zero_point, torch_type) = X
        if not isinstance(X, torch.Tensor):
            X = torch.from_numpy(X)
        if (X.device.type == 'cuda') and (torch.backends.quantized.engine == 'qnnpack'):
            return
        # Quantizes the reference to account for max error.
        # q_min and q_max only depend on the initial torch_type.
        q_min, q_max = torch.iinfo(torch_type).min, torch.iinfo(torch_type).max

        for op_group in test_configs:
            ref_op = op_group['reference_fn']
            for q_op in op_group['quantized_fn']:

                for memory_format in (torch.channels_last, torch.contiguous_format):
                    if memory_format == torch.channels_last and len(X.shape) != 4:
                        continue
                    X = X.to(memory_format=memory_format)

                    # Retrieves the inplace keyword arguments
                    # some functions require inplace=True to test in-place.
                    # copy.copy is needed because these are modified in place
                    extra_kwargs = \
                        copy.copy(op_group.get('extra_kwargs', {}))
                    output_is_observed = \
                        copy.copy(op_group.get('output_is_observed', False))

                    # Quantizes and dequantizes to account for max error.
                    qX = torch.quantize_per_tensor(X, scale=scale, zero_point=zero_point,
                                                   dtype=torch_type)
                    dqX = qX.dequantize()
                    dqY_hat = ref_op(dqX.clone(), **extra_kwargs)

                    # Adjusts output_scale if needed.
                    # The output_scale determines the quantization scale for functions that
                    # have a constrained output range. e.x. sigmoid ranges from 0 to 1.
                    output_scale = scale
                    if 'output_range' in op_group:
                        (f_min, f_max) = op_group['output_range']
                        output_scale = (f_max - f_min) / (q_max - q_min + 1.0)

                    # Adjusts output_zero_point if needed (see explanation for the
                    # change_zero_point parameter above).
                    # output_zero_point determines the additional offset that will be
                    # added to a scaled value during quantization.
                    if op_group.get('change_zero_point', False):
                        output_zero_point = 0 if torch_type == torch.qint32 else q_min
                    else:
                        output_zero_point = zero_point

                    # Quantizes the dequantized version of Y_hat.
                    qY_hat = torch.quantize_per_tensor(dqY_hat, scale=output_scale,
                                                       zero_point=output_zero_point,
                                                       dtype=torch_type)

                    if output_is_observed:
                        extra_kwargs.update({'output_scale': output_scale, 'output_zero_point': output_zero_point})

                    # Finds qY using in-place or non-in-place quantized operators.
                    qY = q_op(qX, **extra_kwargs)

                    self.assertEqual(qY, qY_hat, msg=f'{fn_name} - {q_op} failed: ({qY} vs. {qY_hat})')