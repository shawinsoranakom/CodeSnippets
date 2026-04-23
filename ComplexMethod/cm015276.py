def test_custom_module_multi_head_attention(self):
        class MultiheadAttentionModel(torch.nn.Module):
            def __init__(self, *args, **kwargs):
                super().__init__()
                self.layer = torch.nn.MultiheadAttention(*args, **kwargs)

            def forward(
                self,
                query,
                key,
                value,
                key_padding_mask: torch.Tensor | None = None,
                need_weights: bool = True,
                attn_mask: torch.Tensor | None = None,
            ):
                return self.layer(query, key, value, key_padding_mask, need_weights, attn_mask)

        qengine = torch.backends.quantized.engine

        min_power = 30
        max_mse = 2

        num_heads = 16
        batch_size = 4
        target_seq_length = 128
        source_seq_length = 64
        qembed_dim = 512  # Must be divisible by the number of heads
        kembed_dim = 128
        vembed_dim = 256

        dropout = 0.0  # This is not supported

        Bias = [False, True]
        Add_bias_kv = [False, True]
        Add_zero_attn = [False, True]

        dtype = np.uint8
        qtype = torch.quint8

        for kdim, vdim in ((kembed_dim, vembed_dim), (None, None)):
            fp_data = [
                torch.randn(target_seq_length, batch_size, qembed_dim),  # Q
                torch.randn(source_seq_length, batch_size,
                            qembed_dim if kdim is None else kembed_dim),  # K
                torch.randn(source_seq_length, batch_size,
                            qembed_dim if vdim is None else vembed_dim)   # V
            ]

            q_data = []
            reduce_range = (qengine in ('x86', 'fbgemm', 'onednn'))
            for idx, x in enumerate(fp_data):
                scale, zero_point = _calculate_dynamic_qparams(
                    x, dtype=dtype, reduce_range=reduce_range)
                x = x.to(torch.float)
                qx = torch.quantize_per_tensor(x, scale=scale,
                                               zero_point=zero_point, dtype=qtype)
                q_data.append(qx)

                # Dequantize the data back for reference
                fp_data[idx] = qx.dequantize()

            with torch.no_grad():
                for bias, add_bias_kv, add_zero_attn in itertools.product(
                        Bias, Add_bias_kv, Add_zero_attn):
                    mha = MultiheadAttentionModel(qembed_dim, num_heads, dropout,
                                                  bias, add_bias_kv, add_zero_attn,
                                                  kdim=kdim, vdim=vdim)
                    mha.eval()

                    # Prepare
                    if qengine_is_onednn():
                        # `reduce_range` is False by default for ONEDNN backend
                        # but the test fails on earlier CPUs without VNNI.
                        # So we use a default qconfig with `reduce_range=True` here
                        mha.qconfig = torch.ao.quantization.get_default_qconfig()
                    else:
                        mha.qconfig = torch.ao.quantization.get_default_qconfig(qengine)
                    mha_prepared = torch.ao.quantization.prepare(
                        mha)

                    # Calibrate
                    y = mha_prepared(*fp_data)
                    y_ref = mha(*fp_data)
                    # Check the result of the prepare
                    self.assertEqual(y_ref[0], y[0])  # Attention
                    self.assertEqual(y_ref[1], y[1])  # Weight

                    # Quantize
                    mha_quantized = torch.ao.quantization.convert(mha_prepared)

                    for name, _param in mha_quantized.named_parameters():
                        self.assertTrue("in_proj_weight" not in name)

                    qy = mha_quantized(*q_data)

                    # Reference result
                    mha.layer = mha_quantized.layer.dequantize()
                    y_ref = mha(*fp_data)

                    snr = _snr(y, qy)
                    for signal, mse, power in snr:
                        self.assertTrue(
                            power > min_power or mse < max_mse,
                            msg=(f"Error is too high: SNR(dB): {power}, "
                                 f"Signal: {signal}, MSE: {mse}; "
                                 f"Run with bias={bias}, "
                                 f"add_bias_kv={add_bias_kv}, "
                                 f"add_zero_attn={add_zero_attn}"))

                    # Verify the result is scriptable
                    mha_quantized_scripted = torch.jit.script(mha_quantized)