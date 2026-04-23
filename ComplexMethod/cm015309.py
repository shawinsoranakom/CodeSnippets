def _test_conv_api_impl(
            self, module_name, qconv_module, conv_module, batch_size,
            in_channels_per_group, input_feature_map_size, out_channels_per_group,
            groups, kernel_size, stride, padding, padding_mode, dilation,
            X_scale, X_zero_point, W_scale, W_zero_point, Y_scale, Y_zero_point,
            use_bias, post_op, use_channelwise, X2_scale=1.0, X2_zero_point=0):
        for i in range(len(kernel_size)):
            assume(input_feature_map_size[i] + 2 * padding[i]
                   >= dilation[i] * (kernel_size[i] - 1) + 1)

        in_channels = in_channels_per_group * groups
        out_channels = out_channels_per_group * groups
        (X, X_q, W, W_q, b) = _make_conv_test_input(
            batch_size, in_channels_per_group, input_feature_map_size,
            out_channels_per_group, groups, kernel_size, X_scale, X_zero_point,
            W_scale, W_zero_point, use_bias, use_channelwise)
        example_input = [X, ]
        example_input_q = [X_q, ]

        if post_op in ["add", "add_relu"]:
            X2, X2_q = _make_conv_add_extra_input_tensor(X2_scale, X2_zero_point, conv_module[0](X).size())
            example_input = [X, X2]
            example_input_q = [X_q, X2_q]

        # Make sure the weight shape is correct
        self.assertTrue(qconv_module.weight().shape == W_q.shape)

        qconv_module.set_weight_bias(W_q, b)
        qconv_module.scale = Y_scale
        qconv_module.zero_point = Y_zero_point

        raw_conv_module = conv_module[0] if post_op in ["relu", "add", "add_relu"] else conv_module
        raw_conv_module.weight.data = W
        if use_bias:
            raw_conv_module.bias.data = b

        # Test members
        self.assertTrue(module_name == qconv_module._get_name(), module_name + " " + qconv_module._get_name())
        self.assertTrue(hasattr(qconv_module, '_packed_params'))
        self.assertTrue(hasattr(qconv_module, 'scale'))
        self.assertTrue(hasattr(qconv_module, 'zero_point'))

        # Test properties
        self.assertEqual(W_q, qconv_module.weight())
        if use_bias:
            self.assertEqual(b, qconv_module.bias())
        self.assertEqual(Y_scale, qconv_module.scale)
        self.assertEqual(Y_zero_point, qconv_module.zero_point)

        # Test forward
        Y_exp = conv_module(*example_input)
        Y_exp = torch.quantize_per_tensor(
            Y_exp, scale=Y_scale, zero_point=Y_zero_point, dtype=torch.quint8)
        Y_act = qconv_module(*example_input_q)

        # Make sure the results match
        # assert_array_almost_equal compares using the following formula:
        #     abs(desired-actual) < 1.5 * 10**(-decimal)
        # (https://numpy.org/doc/stable/reference/generated/numpy.testing.assert_almost_equal.html)
        # We use decimal = 0 to ignore off-by-1 differences between reference
        # and test. Off-by-1 differences arise due to the order of round and
        # zero_point addition operation, i.e., if addition followed by round is
        # used by reference and round followed by addition is used by test, the
        # results may differ by 1.
        # For example, the result of round(2.5) + 1 is 3 while round(2.5 + 1) is
        # 4 assuming the rounding mode is round-to-nearest, ties-to-even.
        # skip numerics checking for reference module
        np.testing.assert_array_almost_equal(
            Y_exp.int_repr().numpy(), Y_act.int_repr().numpy(), decimal=0)

        # Test serialization of quantized Conv Module using state_dict
        model_dict = qconv_module.state_dict()
        self.assertEqual(model_dict['weight'], W_q)
        if use_bias:
            self.assertEqual(model_dict['bias'], b)
        bytes_io = io.BytesIO()
        torch.save(model_dict, bytes_io)
        for weights_only in [True, False]:
            bytes_io.seek(0)
            loaded_dict = torch.load(bytes_io, weights_only=weights_only)
            for key in loaded_dict:
                self.assertEqual(model_dict[key], loaded_dict[key])
            loaded_qconv_module = type(qconv_module)(
                in_channels, out_channels, kernel_size, stride, padding, dilation,
                groups, use_bias, padding_mode=padding_mode)
            loaded_qconv_module.load_state_dict(loaded_dict)

            self.assertTrue(dir(loaded_qconv_module) == dir(qconv_module))
            self.assertTrue(module_name == loaded_qconv_module._get_name())
            self.assertTrue(hasattr(loaded_qconv_module, '_packed_params'))
            self.assertTrue(hasattr(loaded_qconv_module, '_weight_bias'))

            self.assertEqual(qconv_module.weight(), loaded_qconv_module.weight())
            if use_bias:
                self.assertEqual(qconv_module.bias(), loaded_qconv_module.bias())
            self.assertEqual(qconv_module.scale, loaded_qconv_module.scale)
            self.assertEqual(qconv_module.zero_point,
                             loaded_qconv_module.zero_point)
            Y_loaded = loaded_qconv_module(*example_input_q)
            np.testing.assert_array_almost_equal(
                Y_exp.int_repr().numpy(), Y_loaded.int_repr().numpy(), decimal=0)

        # Test serialization
        b = io.BytesIO()
        torch.save(qconv_module, b)
        b.seek(0)
        # weights_only=False as this is legacy code that saves the model
        loaded_conv = torch.load(b, weights_only=False)

        self.assertEqual(loaded_conv.bias(), qconv_module.bias())
        self.assertEqual(loaded_conv.scale, qconv_module.scale)
        self.assertEqual(loaded_conv.zero_point,
                         qconv_module.zero_point)

        # Test copy and deepcopy
        copied_conv = copy.copy(qconv_module)
        self.assertEqual(copied_conv.bias(), qconv_module.bias())
        self.assertEqual(copied_conv.scale, qconv_module.scale)
        self.assertEqual(copied_conv.zero_point,
                         qconv_module.zero_point)
        Y_copied = copied_conv(*example_input_q)
        np.testing.assert_array_almost_equal(
            Y_exp.int_repr().numpy(), Y_copied.int_repr().numpy(), decimal=0)

        deepcopied_conv = copy.deepcopy(qconv_module)
        self.assertEqual(deepcopied_conv.bias(), qconv_module.bias())
        self.assertEqual(deepcopied_conv.scale, qconv_module.scale)
        self.assertEqual(deepcopied_conv.zero_point,
                         qconv_module.zero_point)
        Y_deepcopied = deepcopied_conv(*example_input_q)
        np.testing.assert_array_almost_equal(
            Y_exp.int_repr().numpy(), Y_deepcopied.int_repr().numpy(), decimal=0)

        # JIT testing
        self.checkScriptable(
            qconv_module, [example_input_q],
            check_save_load=True)

        class _FusedModule_two_input_args(torch.ao.nn.intrinsic._FusedModule):
            # Help Module for ConvAdd2d since torch.ao.nn.intrinsic._FusedModule only support one input arg
            def forward(self, x1, x2):
                input = self[0](x1, x2)
                return input

        # Test from_float
        fused_conv_module = _FusedModule_two_input_args(conv_module) \
            if post_op in ["add", "add_relu"] else torch.ao.nn.intrinsic._FusedModule(conv_module)

        fused_conv_module.qconfig = torch.ao.quantization.default_qconfig
        torch.ao.quantization.prepare(fused_conv_module, inplace=True)
        example_input[0] = example_input[0].float()
        fused_conv_module(*example_input)
        converted_qconv_module = fused_conv_module
        reference_mapping = get_default_static_quant_module_mappings()
        reference_mapping[type(conv_module)] = type(qconv_module)
        torch.ao.quantization.convert(converted_qconv_module, mapping=reference_mapping, inplace=True)

        # Smoke test to make sure the module actually runs
        if use_bias:
            self.assertEqual(conv_module[0].bias if (post_op in ["relu", "add", "add_relu"]) else conv_module.bias,
                             converted_qconv_module[0].bias())
        # Smoke test extra_repr
        self.assertTrue(module_name == converted_qconv_module[0]._get_name())