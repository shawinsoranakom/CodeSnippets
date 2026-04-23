def test_custom_module_lstm(self):
        class QuantizableLSTMSplitGates(torch.ao.nn.quantizable.LSTM):
            @classmethod
            def from_float(cls, other, qconfig=None):
                return super().from_float(other, qconfig, split_gates=True)

        qengine = torch.backends.quantized.engine

        batch_size = 4
        seq_len = 8
        input_size = 12

        hidden_size = 8
        num_layers = 2

        dropout = 0  # This is not supported

        Bias = [False, True]
        Batch_first = [False, True]
        Bidirectional = [False, True]
        Split_gates = [False, True]

        dtype = np.uint8
        qtype = torch.quint8

        x = np.random.randn(seq_len, batch_size, input_size)
        scale, zero_point = _calculate_dynamic_qparams(x, dtype=dtype)
        x = torch.from_numpy(x).to(torch.float)
        qx = torch.quantize_per_tensor(x, scale=scale, zero_point=zero_point,
                                       dtype=qtype)
        x = qx.dequantize()

        with torch.no_grad():
            for bias, batch_first, bidirectional, split_gates in itertools.product(
                    Bias, Batch_first, Bidirectional, Split_gates):
                # Assume 12dB is sufficient for functional equivalence
                # Without the bias, linear performs poorly
                min_power = 10 if bias else 5
                max_mse = 5e-6 if bias else 5e-1

                if batch_first:
                    x = x.reshape(batch_size, seq_len, input_size)
                    qx = qx.reshape(batch_size, seq_len, input_size)
                else:
                    x = x.reshape(seq_len, batch_size, input_size)
                    qx = qx.reshape(seq_len, batch_size, input_size)

                lstm = torch.nn.Sequential(
                    torch.nn.LSTM(input_size, hidden_size,
                                  num_layers=num_layers,
                                  bias=bias, batch_first=batch_first,
                                  dropout=dropout,
                                  bidirectional=bidirectional))
                lstm.eval()
                y_ref = lstm(x)

                # Prepare
                lstm.qconfig = torch.ao.quantization.get_default_qconfig(qengine)
                custom_config_dict = (
                    None
                    if not split_gates
                    else {  # switch to class with split_gates True via from_float
                        "float_to_observed_custom_module_class": {
                            torch.nn.LSTM: QuantizableLSTMSplitGates
                        },
                        "observed_to_quantized_custom_module_class": {
                            QuantizableLSTMSplitGates: torch.ao.nn.quantized.LSTM,
                        },
                    }
                )
                lstm_prepared = torch.ao.quantization.prepare(
                    lstm, prepare_custom_config_dict=custom_config_dict
                )
                self.assertTrue(hasattr(lstm_prepared[0], 'layers'))
                self.assertEqual(num_layers, len(lstm_prepared[0].layers))
                self.assertEqual(
                    lstm_prepared[0].layers[0].layer_fw.cell.split_gates, split_gates
                )
                if not isinstance(lstm_prepared[0], torch.ao.nn.quantizable.LSTM):
                    raise AssertionError(
                        f"Expected lstm_prepared[0] to be an instance of "
                        f"torch.ao.nn.quantizable.LSTM, got {type(lstm_prepared[0])}"
                    )

                # Calibrate
                y = lstm_prepared(x)
                self.assertEqual(y_ref, y)

                # Quantize
                lstm_quantized = torch.ao.quantization.convert(
                    lstm_prepared, convert_custom_config_dict=custom_config_dict
                )
                if type(lstm_quantized[0]) is not torch.ao.nn.quantized.LSTM:
                    raise AssertionError(
                        f"Expected type(lstm_quantized[0]) to be "
                        f"torch.ao.nn.quantized.LSTM, got {type(lstm_quantized[0])}"
                    )
                qy = lstm_quantized(qx)

                snr = _snr(y, qy)
                snr = [snr[0]] + snr[1]

                for signal, mse, power in snr:
                    self.assertTrue(
                        power > min_power or mse < max_mse,
                        msg=(f"Error is too high: SNR(dB): {power}, "
                             f"Signal: {signal}, MSE: {mse}"))

                # Trace
                jit_qmodule = torch.jit.trace(lstm_quantized, qx)

                # Script
                jit_qmodule = torch.jit.script(lstm_quantized)