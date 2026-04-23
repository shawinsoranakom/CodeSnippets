def test_static_lstm_with_custom_fixed_qparams(self):
        """
        Test statically quantized LSTM with custom fixed qparams assigned to each of the
        inner submodules. This flow requires users to extend `torch.ao.nn.quantizable.LSTM`
        and use the child class in the custom module mapping.
        """
        class MyModel(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.my_lstm = torch.nn.LSTM(50, 50, 1)

            def forward(self, inputs: torch.Tensor, h0: torch.Tensor, c0: torch.Tensor):
                x = self.my_lstm(inputs, (h0, c0))
                return x

        # Construct a BackendConfig that supports qint32 for certain ops
        # TODO: build a BackendConfig from scratch instead of modifying an existing one
        qint32_dtype_config = DTypeConfig(input_dtype=torch.qint32, output_dtype=torch.qint32)
        my_backend_config = get_qnnpack_backend_config()
        for config in my_backend_config.configs:
            if config.pattern in [torch.nn.Sigmoid, torch.nn.Tanh, torch.add, torch.mul]:
                config.add_dtype_config(qint32_dtype_config)

        class UserObservedLSTM(torch.ao.nn.quantizable.LSTM):
            """
            Example of user provided LSTM implementation that assigns fixed qparams
            to the inner ops.
            """
            @classmethod
            def from_float(cls, float_lstm):
                if not isinstance(float_lstm, cls._FLOAT_MODULE):
                    raise AssertionError(f"Expected instance of {cls._FLOAT_MODULE}, got {type(float_lstm)}")
                # uint16, [-16, 16)
                linear_output_obs_ctr = FixedQParamsObserver.with_args(scale=2 ** -11, zero_point=2 ** 15, dtype=torch.qint32)
                # uint16, [0, 1)
                sigmoid_obs_ctr = FixedQParamsObserver.with_args(scale=2 ** -16, zero_point=0, dtype=torch.qint32)
                # uint16, [-1, 1)
                tanh_obs_ctr = FixedQParamsObserver.with_args(scale=2 ** -15, zero_point=2 ** 15, dtype=torch.qint32)
                # int16, [-16, 16)
                cell_state_obs_ctr = FixedQParamsObserver.with_args(scale=2 ** -11, zero_point=0, dtype=torch.qint32)
                # uint8, [-1, 1)
                hidden_state_obs_ctr = FixedQParamsObserver.with_args(scale=2 ** -7, zero_point=2 ** 7, dtype=torch.quint8)
                example_inputs = (torch.rand(5, 3, 50), (torch.rand(1, 3, 50), torch.randn(1, 3, 50)))
                return torch.ao.quantization.fx.lstm_utils._get_lstm_with_individually_observed_parts(
                    float_lstm=float_lstm,
                    example_inputs=example_inputs,
                    backend_config=my_backend_config,
                    linear_output_obs_ctr=linear_output_obs_ctr,
                    sigmoid_obs_ctr=sigmoid_obs_ctr,
                    tanh_obs_ctr=tanh_obs_ctr,
                    cell_state_obs_ctr=cell_state_obs_ctr,
                    hidden_state_obs_ctr=hidden_state_obs_ctr,
                )

        class UserQuantizedLSTM(torch.ao.nn.quantized.LSTM):
            """
            Example of user provided LSTM implementation that produces a reference
            quantized module from a `UserObservedLSTM`.
            """
            @classmethod
            def from_observed(cls, observed_lstm):
                if not isinstance(observed_lstm, cls._FLOAT_MODULE):
                    raise AssertionError(f"Expected instance of {cls._FLOAT_MODULE}, got {type(observed_lstm)}")
                return torch.ao.quantization.fx.lstm_utils._get_reference_quantized_lstm_module(
                    observed_lstm=observed_lstm,
                    backend_config=my_backend_config,
                )

        # FX graph mode quantization
        m = MyModel()
        qconfig_mapping = get_default_qconfig_mapping("qnnpack")
        example_inputs = (torch.rand(5, 3, 50), torch.rand(1, 3, 50), torch.randn(1, 3, 50))
        prepare_custom_config = PrepareCustomConfig() \
            .set_float_to_observed_mapping(torch.nn.LSTM, UserObservedLSTM)
        convert_custom_config = ConvertCustomConfig() \
            .set_observed_to_quantized_mapping(torch.ao.nn.quantizable.LSTM, UserQuantizedLSTM)
        prepared = prepare_fx(
            m,
            qconfig_mapping,
            example_inputs,
            prepare_custom_config,
            backend_config=my_backend_config,
        )
        prepared(*example_inputs)
        converted = convert_fx(
            prepared,
            convert_custom_config,
            backend_config=my_backend_config,
        )
        converted(*example_inputs)

        # Find the patterns [dq - op - q_to_specific_dtype] in the graph and
        # verify that qparams and dtypes are set correctly in the quantize ops
        node_name_to_expected_quantize_args = {
            "igates": (None, None, torch.quint8),
            "hgates": (None, None, torch.quint8),
            "add": (2 ** -11, 2 ** 15, torch.qint32),  # gates.add
            "input_gate": (2 ** -16, 0, torch.qint32),
            "forget_gate": (2 ** -16, 0, torch.qint32),
            "cell_gate": (2 ** -15, 2 ** 15, torch.qint32),
            "output_gate": (2 ** -16, 0, torch.qint32),
            "mul": (2 ** -11, 0, torch.qint32),  # fgate_cx.mul
            "mul_1": (2 ** -11, 0, torch.qint32),  # igate_cgate.mul
            "add_1": (2 ** -11, 0, torch.qint32),  # fgate_cx_igate_cgate.add
            "mul_2": (2 ** -7, 2 ** 7, torch.quint8),  # ogate_cy.mul
        }
        cell = converted.my_lstm.layers.get_submodule("0").layer_fw.cell
        matched_names = set()
        for node in cell.graph.nodes:
            if node.name not in node_name_to_expected_quantize_args:
                continue
            matched_names.add(node.name)
            # Match preceding dequantize
            self.assertTrue(all(arg.target == "dequantize" for arg in node.args))
            # Match following quantize with the specific qparams and dtypes
            expected_scale, expected_zp, expected_dtype = node_name_to_expected_quantize_args[node.name]
            for user in node.users:
                self.assertEqual(user.target, torch.quantize_per_tensor)
                if expected_scale is not None:
                    self.assertEqual(getattr(cell, user.args[1].target), expected_scale)
                if expected_zp is not None:
                    self.assertEqual(getattr(cell, user.args[2].target), expected_zp)
                self.assertEqual(user.args[-1], expected_dtype)
        # Ensure all patterns were matched
        self.assertEqual(matched_names, set(node_name_to_expected_quantize_args.keys()))