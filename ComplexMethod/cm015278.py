def test_qlstmGRU(self, num_batches, input_size, hidden_size,
                      num_directions, per_channel_quant):
        # We test only for seq length of 1 and num layers of 1 as dynamic quantization occurs multiple times
        # within the LSTM op and we do not model the quantization between multiple calls of the linear op within the
        # lstm op
        seq_len = 1

        for rnn_type in ['LSTM', 'GRU']:
            for dtype in [torch.qint8, torch.float16]:
                # Fp16 quantization is not supported for qnnpack or onednn
                if torch.backends.quantized.engine in ('qnnpack', 'onednn') and dtype == torch.float16:
                    continue

                if torch.backends.quantized.engine == 'qnnpack':
                    reduce_range = False
                else:
                    reduce_range = True
                Xq, Hq, Cq = self._get_rnn_inputs(seq_len, num_batches, input_size,
                                                  hidden_size, num_directions, reduce_range)
                Wq1, Wq2, b1, b2 = self._get_rnn_weights_and_bias(input_size,
                                                                  hidden_size,
                                                                  num_directions,
                                                                  per_channel_quant,
                                                                  rnn_type)
                if dtype == torch.qint8:
                    packed_ih = torch.ops.quantized.linear_prepack(Wq1, b1)
                    packed_hh = torch.ops.quantized.linear_prepack(Wq2, b2)
                    cell_params = torch.ops.quantized.make_quantized_cell_params_dynamic(
                        packed_ih, packed_hh, b1, b2, reduce_range)
                    W_ref1 = Wq1.dequantize()
                    W_ref2 = Wq2.dequantize()

                else:
                    packed_ih = torch.ops.quantized.linear_prepack_fp16(Wq1.dequantize(), b1)
                    packed_hh = torch.ops.quantized.linear_prepack_fp16(Wq2.dequantize(), b2)
                    cell_params = torch.ops.quantized.make_quantized_cell_params_fp16(packed_ih, packed_hh)
                    W_ref1 = Wq1.dequantize().to(torch.float16).to(torch.float32)
                    W_ref2 = Wq2.dequantize().to(torch.float16).to(torch.float32)

                if rnn_type == 'LSTM':
                    if num_directions > 1:
                        result_ref = _VF.lstm(Xq.dequantize(),
                                              (Hq.dequantize(), Cq.dequantize()),
                                              [W_ref1, W_ref2, b1, b2, W_ref1, W_ref2, b1, b2],
                                              True,
                                              1,
                                              0,
                                              False,
                                              num_directions > 1,
                                              False)

                        result_dynamic = torch.quantized_lstm(Xq.dequantize(),
                                                              (Hq.dequantize(), Cq.dequantize()),
                                                              ([cell_params, cell_params]),
                                                              True,
                                                              1,
                                                              0,
                                                              False,
                                                              True,
                                                              False,
                                                              dtype=torch.qint8,
                                                              use_dynamic=True)
                    else:
                        result_ref = _VF.lstm(Xq.dequantize(),
                                              (Hq.dequantize(), Cq.dequantize()),
                                              [W_ref1, W_ref2, b1, b2],
                                              True,
                                              1,
                                              0,
                                              False,
                                              num_directions > 1,
                                              False)

                        result_dynamic = torch.quantized_lstm(Xq.dequantize(),
                                                              (Hq.dequantize(), Cq.dequantize()),
                                                              ([cell_params]),
                                                              True,
                                                              1,
                                                              0,
                                                              False,
                                                              num_directions > 1,
                                                              False,
                                                              dtype=torch.qint8,
                                                              use_dynamic=True)

                if rnn_type == 'GRU':
                    if num_directions > 1:
                        result_ref = _VF.gru(Xq.dequantize(),
                                             Hq.dequantize(),
                                             [W_ref1, W_ref2, b1, b2, W_ref1, W_ref2, b1, b2],
                                             True,
                                             1,
                                             0,
                                             False,
                                             True,
                                             False)

                        result_dynamic = torch.quantized_gru(Xq.dequantize(),
                                                             Hq.dequantize(),
                                                             ([cell_params, cell_params]),
                                                             True,
                                                             1,
                                                             0,
                                                             False,
                                                             True,
                                                             False)
                    else:
                        result_ref = _VF.gru(Xq.dequantize(),
                                             Hq.dequantize(),
                                             [W_ref1, W_ref2, b1, b2],
                                             True,
                                             1,
                                             0,
                                             False,
                                             False,
                                             False)

                        result_dynamic = torch.quantized_gru(Xq.dequantize(),
                                                             Hq.dequantize(),
                                                             ([cell_params]),
                                                             True,
                                                             1,
                                                             0,
                                                             False,
                                                             False,
                                                             False)

                self.assertEqual(result_ref[0], result_dynamic[0], msg="torch.quantized_lstm results are off")