def _test_qconv_unpack_impl(self, qconv_prepack_fn, qconv_unpack_fn, inputs,
                                strides, i_pads, o_pads, channelwise):
        (X_data, W_data, bias_data, groups, transposed) = inputs
        (X, (X_scale, X_zero_point, X_qtype)) = X_data
        (W, (W_scale, W_zero_point, W_qtype)) = W_data
        (bias, (bias_scale, bias_zero_point, bias_qtype)) = bias_data

        W = torch.from_numpy(W).float()
        bias = torch.from_numpy(bias).float()
        if channelwise and transposed:
            # currently transposed conv and per-channel per quantization does not work
            return
        # ONEDNN only supports symmetric quantization of weight and zero output padding
        if qengine_is_onednn():
            W_zero_point = 0
            o_pads = len(o_pads) * [0] if o_pads is not None else None
        if channelwise:
            if transposed:
                output_channels = W.shape[1]  # IC OC/G
            else:
                output_channels = W.shape[0]  # OC IC/G
            W_scale = torch.tensor([W_scale] * output_channels)
            W_zero_point = torch.tensor([W_zero_point] * output_channels)
            W_q = torch.quantize_per_channel(
                W, scales=W_scale, zero_points=W_zero_point,
                axis=int(transposed), dtype=W_qtype)
        else:
            W_q = torch.quantize_per_tensor(
                W, scale=W_scale, zero_point=W_zero_point, dtype=W_qtype)

        if isinstance(strides, int):
            dilations = [1]
        else:
            dilations = (1,) * len(strides)

        if transposed:
            W_packed = qconv_prepack_fn(W_q, bias, strides, i_pads, o_pads,
                                        dilations, groups)
        else:
            W_packed = qconv_prepack_fn(W_q, bias, strides, i_pads, dilations,
                                        groups)
        (W_unpacked, bias) = qconv_unpack_fn(W_packed)

        # Assert equal
        np.testing.assert_equal(W_q.int_repr().numpy(),
                                W_unpacked.int_repr().numpy())
        if channelwise:
            np.testing.assert_array_almost_equal(
                np.float32(W_q.q_per_channel_scales().numpy()),
                np.float32(W_unpacked.q_per_channel_scales().numpy()),
                decimal=4)
            np.testing.assert_equal(W_q.q_per_channel_zero_points(
            ).numpy(), W_unpacked.q_per_channel_zero_points().numpy())
        else:
            np.testing.assert_equal(np.float32(
                W_q.q_scale()), np.float32(W_unpacked.q_scale()))
            np.testing.assert_equal(
                W_q.q_zero_point(), W_unpacked.q_zero_point())