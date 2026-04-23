def test_input_weight_eq_observer(self, ndim, input_qdtype, input_qscheme, weight_qdtype, weight_qscheme):
        sizes = []
        for _ in range((ndim - 1) * 2):
            sizes.append(np.random.randint(2, 10))

        channel = np.random.randint(1, 10)
        if ndim == 2:
            x = np.random.random(size=(sizes[0], channel))
            w = np.random.random(size=(sizes[1], channel))
        elif ndim == 3:
            x = np.random.random(size=(sizes[0], channel, sizes[1]))
            w = np.random.random(size=(sizes[2], channel, sizes[3]))
        elif ndim == 4:
            x = np.random.random(size=(sizes[0], channel, sizes[1], sizes[2]))
            w = np.random.random(size=(sizes[3], channel, sizes[4], sizes[5]))
        elif ndim == 5:
            x = np.random.random(size=(sizes[0], channel, sizes[1], sizes[2], sizes[3]))
            w = np.random.random(size=(sizes[4], channel, sizes[5], sizes[6], sizes[7]))

        x = (x * 10).round(decimals=2).astype(np.float32)
        w = (w * 10).round(decimals=2).astype(np.float32)

        input_eq_obs = _InputEqualizationObserver(dtype=input_qdtype, qscheme=input_qscheme)
        weight_eq_obs = _WeightEqualizationObserver(dtype=weight_qdtype, qscheme=weight_qscheme)

        ret_x = input_eq_obs(torch.tensor(x))
        ret_w = weight_eq_obs(torch.tensor(w))
        self.assertEqual((ret_x, ret_w), (x, w))

        # Check the min/max input columns are correct
        ref_min_inputs, ref_max_inputs = self.channel_minmax(x)
        min_inputs, max_inputs = input_eq_obs.get_input_minmax()
        self.assertEqual(min_inputs, torch.tensor(ref_min_inputs, dtype=torch.float32))
        self.assertEqual(max_inputs, torch.tensor(ref_max_inputs, dtype=torch.float32))

        # Check the min/max weight columns are correct
        ref_min_weights_col, ref_max_weights_col = self.channel_minmax(w)
        min_weights_col, max_weights_col = weight_eq_obs.get_weight_col_minmax()
        self.assertEqual(min_weights_col, torch.tensor(ref_min_weights_col, dtype=torch.float32))
        self.assertEqual(max_weights_col, torch.tensor(ref_max_weights_col, dtype=torch.float32))

        # Check the equalization scale is correct
        equalization_scale = calculate_equalization_scale(input_eq_obs, weight_eq_obs)
        ref_equalization_scale = np.sqrt((ref_max_weights_col - ref_min_weights_col) /
                                         (ref_max_inputs - ref_min_inputs))
        self.assertEqual(equalization_scale, torch.tensor(ref_equalization_scale, dtype=torch.float32))

        input_eq_obs.set_equalization_scale(equalization_scale)
        weight_eq_obs.set_equalization_scale(equalization_scale)

        # Check the input scale/zero-point values
        min_input_scaled, max_input_scaled = input_eq_obs.calculate_scaled_minmax()
        input_quant_obs = MinMaxObserver(dtype=input_qdtype, qscheme=input_qscheme)
        input_quant_obs.min_val = min_input_scaled
        input_quant_obs.max_val = max_input_scaled
        input_qparams = input_quant_obs.calculate_qparams()

        ref_min_input_scaled = np.min(ref_min_inputs * ref_equalization_scale)
        ref_min_input_scaled = min(0, ref_min_input_scaled)
        ref_max_input_scaled = np.max(ref_max_inputs * ref_equalization_scale)
        ref_max_input_scaled = max(0, ref_max_input_scaled)

        if input_qscheme == torch.per_tensor_symmetric:
            ref_scale = 2 * max(abs(ref_min_input_scaled), ref_max_input_scaled) / 255
            ref_zero_point = 0 if input_qdtype is torch.qint8 else 128
        else:
            ref_scale = (ref_max_input_scaled - ref_min_input_scaled) / 255
            quant_min = -128 if input_qdtype is torch.qint8 else 0
            quant_max = 127 if input_qdtype is torch.qint8 else 255
            ref_zero_point = quant_min - np.round(ref_min_input_scaled / ref_scale)
            np.clip(ref_zero_point, quant_min, quant_max)

        self.assertEqual(input_qparams[0].item(), ref_scale, atol=1e-5, rtol=0)
        self.assertEqual(input_qparams[1].item(), ref_zero_point)

        # During input-weight equalization, we will scale the weights so that
        # the following weight quantized observer will have the correct scaled qparams
        # Check the weight scale/zero-point values of the quantized observer
        weight_quant_obs = PerChannelMinMaxObserver(ch_axis=1, dtype=weight_qdtype, qscheme=weight_qscheme)

        # Scale the weights for input-weight equalization
        new_shape = [1] * w.ndim
        new_shape[1] = w.shape[1]
        ref_w_scaled = w * np.reciprocal(ref_equalization_scale.reshape(tuple(new_shape)))

        w = torch.tensor(w)
        new_shape[1] = w.size(1)
        w_scaled = torch.mul(w, torch.reciprocal(equalization_scale.view(new_shape)))

        self.assertEqual(w_scaled, ref_w_scaled)

        # Call forward on the weight quantization observer
        weight_quant_obs(w_scaled)

        # Check the min/max weight rows are correct
        ref_min_weights_scaled, ref_max_weights_scaled = self.channel_minmax(ref_w_scaled)
        self.assertEqual(weight_quant_obs.min_val, torch.tensor(ref_min_weights_scaled, dtype=torch.float32))
        self.assertEqual(weight_quant_obs.max_val, torch.tensor(ref_max_weights_scaled, dtype=torch.float32))

        weight_qparams = weight_quant_obs.calculate_qparams()

        if weight_qscheme == torch.per_channel_symmetric:
            ref_min_weights_scaled = np.minimum(np.zeros(ref_min_weights_scaled.shape), ref_min_weights_scaled)
            ref_max_weights_scaled = np.maximum(np.zeros(ref_max_weights_scaled.shape), ref_max_weights_scaled)

            ref_scales = 2 * np.maximum(np.abs(ref_min_weights_scaled), ref_max_weights_scaled) / 255
            ref_zero_points = np.zeros_like(
                ref_scales) if weight_qdtype is torch.qint8 else np.ones_like(ref_scales) * 128
        elif weight_qscheme == torch.per_channel_affine_float_qparams:
            ref_scales = (ref_max_weights_scaled - ref_min_weights_scaled) / 255
            ref_scales = np.where(ref_scales > 1e-7, ref_scales, np.ones_like(ref_scales))
            ref_zero_points = -1 * ref_min_weights_scaled / ref_scales
        else:
            ref_min_weights_scaled = np.minimum(np.zeros_like(ref_min_weights_scaled), ref_min_weights_scaled)
            ref_max_weights_scaled = np.maximum(np.zeros_like(ref_max_weights_scaled), ref_max_weights_scaled)

            ref_scales = (ref_max_weights_scaled - ref_min_weights_scaled) / 255
            ref_zero_points = -128 if weight_qdtype is torch.qint8 else 0
            ref_zero_points = ref_zero_points - np.round(ref_min_weights_scaled / ref_scales)

        self.assertEqual(weight_qparams[0], torch.tensor(
            ref_scales, dtype=weight_qparams[0].dtype), rtol=1e-5, atol=0.0001)
        self.assertEqual(weight_qparams[1], torch.tensor(
            ref_zero_points, dtype=weight_qparams[1].dtype), rtol=1e-5, atol=1)