def test_lstm_api(self, dtype, bidirectional):
        r"""Test execution and serialization for dynamic quantized lstm modules on int8 and fp16
        """
        # Check that module matches the numerics of the op and ensure that module can be
        # instantiated for all engines and dtypes
        seq_len = 4
        batch = 2
        input_size = 3
        hidden_size = 7
        num_layers = 2
        bias = True
        weight_keys = []
        bias_keys = []
        num_directions = 2 if bidirectional else 1
        for layer in range(num_layers):
            for direction in range(num_directions):
                suffix = '_reverse' if direction == 1 else ''
                key_name1 = f'weight_ih_l{layer}{suffix}'
                key_name2 = f'weight_hh_l{layer}{suffix}'
                weight_keys.append(key_name1)
                weight_keys.append(key_name2)
                key_name1 = f'bias_ih_l{layer}{suffix}'
                key_name2 = f'bias_hh_l{layer}{suffix}'
                bias_keys.append(key_name1)
                bias_keys.append(key_name2)

        if not (dtype == torch.float16 and torch.backends.quantized.engine in ("qnnpack", "onednn")):
            # fp16 dynamic quant is not supported for qnnpack or onednn
            x = torch.randn(seq_len, batch, input_size)
            h = torch.randn(num_layers * (bidirectional + 1), batch, hidden_size)
            c = torch.randn(num_layers * (bidirectional + 1), batch, hidden_size)
            cell_dq = torch.ao.nn.quantized.dynamic.LSTM(input_size=input_size,
                                                         hidden_size=hidden_size,
                                                         num_layers=num_layers,
                                                         bias=bias,
                                                         batch_first=False,
                                                         dropout=0.0,
                                                         bidirectional=bidirectional,
                                                         dtype=dtype)
            ref_dq = torch.ao.nn.quantized.dynamic.LSTM(input_size=input_size,
                                                        hidden_size=hidden_size,
                                                        num_layers=num_layers,
                                                        bias=bias,
                                                        batch_first=False,
                                                        dropout=0.0,
                                                        bidirectional=bidirectional,
                                                        dtype=dtype)

            _all_params = ([m.param for m in cell_dq._all_weight_values])
            result = torch.quantized_lstm(x, (h, c),
                                          _all_params,
                                          cell_dq.bias,
                                          cell_dq.num_layers,
                                          float(cell_dq.dropout),
                                          False,
                                          bidirectional,
                                          False,
                                          dtype=dtype,
                                          use_dynamic=True)


            y, (h, c) = cell_dq(x, (h, c))
            self.assertEqual(result[0], y)
            self.assertEqual(result[1], h)
            self.assertEqual(result[2], c)
            x = torch.randn(10, 20, 3)
            self.check_eager_serialization(cell_dq, ref_dq, [x])
            self.check_weight_bias_api(cell_dq, weight_keys, bias_keys)