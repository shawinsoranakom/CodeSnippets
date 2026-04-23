def test_mixed_dtypes(self):
        """
        Test that multiple dtypes can be used in the same model for different layers,
        and the dtypes will be converted correctly between the layers.
        """
        class MyModule(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.linear1 = torch.nn.Linear(5, 5)
                self.linear2 = torch.nn.Linear(5, 5)
                self.sigmoid = torch.nn.Sigmoid()
                self.tanh = torch.nn.Tanh()
                self.float_functional = torch.ao.nn.quantized.FloatFunctional()

            def forward(self, x: torch.Tensor):
                x = self.linear1(x)  # qint32
                x = self.linear2(x)  # quint8
                linear2 = x
                x = self.sigmoid(x)  # back to qint32
                x = self.tanh(x)  # back to quint8
                x = self.float_functional.add(linear2, x)  # adding two quint8's together
                return x

        def make_qconfig(scale, zp, dtype):
            return QConfig(
                activation=FixedQParamsObserver.with_args(scale=scale, zero_point=zp, dtype=dtype),
                weight=torch.ao.quantization.default_weight_observer)

        # Set up a QConfigMapping that specifies different qparams and dtypes for different layers
        qconfig_mapping = QConfigMapping() \
            .set_global(get_default_qconfig("qnnpack")) \
            .set_module_name("linear1", make_qconfig(1234, 11, torch.qint32)) \
            .set_module_name("linear2", make_qconfig(2345, 22, torch.quint8)) \
            .set_object_type(torch.nn.Sigmoid, make_qconfig(3456, 33, torch.qint32)) \
            .set_object_type(torch.nn.Tanh, make_qconfig(4567, 44, torch.quint8))

        # Set up BackendConfig that supports the dtypes configured in the above QConfigMapping
        weighted_op_qint32_dtype_config = DTypeConfig(
            input_dtype=torch.qint32,
            output_dtype=torch.qint32,
            weight_dtype=torch.qint8,
            bias_dtype=torch.float,
        )
        fixed_qparams_op_quint8_dtype_config = DTypeConfig(
            input_dtype=torch.quint8,
            output_dtype=torch.quint8,
        )
        fixed_qparams_op_qint32_dtype_config = DTypeConfig(
            input_dtype=torch.qint32,
            output_dtype=torch.qint32,
        )
        backend_config = get_qnnpack_backend_config()
        for config in backend_config.configs:
            if config.pattern == torch.nn.Linear:
                config.add_dtype_config(weighted_op_qint32_dtype_config)
            elif config.pattern in [torch.nn.Sigmoid, torch.nn.Tanh]:
                config.add_dtype_config(fixed_qparams_op_quint8_dtype_config)
                config.add_dtype_config(fixed_qparams_op_qint32_dtype_config)

        # Produce the reference quantized model
        m = MyModule()
        example_inputs = (torch.rand(5, 5),)
        prepared = prepare_fx(m, qconfig_mapping, example_inputs, backend_config=backend_config)
        prepared(*example_inputs)  # calibrate
        converted = convert_to_reference_fx(prepared, backend_config=backend_config)
        converted(*example_inputs)

        # Verify that the reference model is correct
        #
        # Reference model until add should be:
        # fp32_input -> q_to_int32 -> [dq -> linear1_fp32 -> q_to_int32] -> dq ->
        # q_to_uint8 -> [dq -> linear2_fp32 -> q_to_uint8] -> dq (linear2_dq) ->
        # q_to_int32 -> [dq -> sigmoid_fp32 -> q_to_int32] -> dq ->
        # q_to_uint8 -> [dq -> tanh_fp32 -> q_to_uint8] -> dq (tanh_dq)
        #
        # Complete reference model with add should be:
        # [(linear2_dq, tanh_dq) -> add_fp32 -> q_to_uint8] -> dq -> fp32_output

        target_to_expected_dtypes = {
            "linear1": torch.qint32,
            "linear2": torch.quint8,
            "sigmoid": torch.qint32,
            "tanh": torch.quint8,
            torch.add: torch.quint8,
        }
        # Find the patterns [dq - op_fp32 - q_to_specific_dtype] in the graph
        linear2_node = tanh_node = None
        for node in converted.graph.nodes:
            if node.target not in target_to_expected_dtypes:
                continue

            # Match preceding dequantize
            self.assertTrue(len(node.args) == 1 or len(node.args) == 2)
            self.assertTrue(all(arg.target == "dequantize" for arg in node.args))

            # Match following quantize with the specific dtypes
            self.assertEqual(len(node.users), 1)
            user = next(iter(node.users.keys()))
            self.assertEqual(user.target, torch.quantize_per_tensor)
            self.assertEqual(user.args[-1], target_to_expected_dtypes[node.target])

            # Match [dq - torch.add(linear2_dq, tanh_dq) - q]
            if node.target == "linear2":
                linear2_node = node
            elif node.target == "tanh":
                tanh_node = node
            elif node.target == torch.add:
                linear2_dq, tanh_dq = node.args
                self.assertEqual(tanh_dq.args[0].args[0], tanh_node)
                self.assertEqual(linear2_dq.args[0].args[0], linear2_node)