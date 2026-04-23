def test_per_channel_observers(self, qdtype, qscheme, ch_axis, reduce_range):
        # reduce_range cannot be true for symmetric quantization with uint8
        if qscheme == torch.per_channel_affine_float_qparams:
            reduce_range = False
        if qdtype == torch.quint8 and qscheme == torch.per_channel_symmetric:
            reduce_range = False
        ObserverList = [PerChannelMinMaxObserver(reduce_range=reduce_range,
                                                 ch_axis=ch_axis,
                                                 dtype=qdtype,
                                                 qscheme=qscheme),
                        MovingAveragePerChannelMinMaxObserver(averaging_constant=0.5,
                                                              reduce_range=reduce_range,
                                                              ch_axis=ch_axis,
                                                              dtype=qdtype,
                                                              qscheme=qscheme)]

        for myobs in ObserverList:
            # Calculate qparams should work for empty observers
            qparams = myobs.calculate_qparams()
            x = torch.tensor(
                [
                    [[[1.0, 2.0], [2.0, 2.5]], [[3.0, 4.0], [4.5, 6.0]]],
                    [[[-4.0, -3.0], [5.0, 5.0]], [[6.0, 3.0], [7.0, 8.0]]],
                ]
            )
            if type(myobs) is MovingAveragePerChannelMinMaxObserver:
                # Scaling the input tensor to model change in min/max values
                # across batches
                result = myobs(0.5 * x)
                result = myobs(1.5 * x)
                self.assertEqual(result, 1.5 * x)
            else:
                result = myobs(x)
                self.assertEqual(result, x)

            qparams = myobs.calculate_qparams()
            ref_min_vals = [[1.0, -4.0], [-4.0, 3.0], [-4.0, 2.0], [-4.0, -3.0]]
            ref_max_vals = [[6.0, 8.0], [5.0, 8.0], [6.0, 8.0], [7.0, 8.0]]
            per_channel_symmetric_ref_scales = [
                [0.04705882, 0.06274509],
                [0.03921569, 0.0627451],
                [0.04705882, 0.0627451],
                [0.05490196, 0.0627451],
            ]
            per_channel_affine_ref_scales = [
                [0.02352941, 0.04705882],
                [0.03529412, 0.03137255],
                [0.03921569, 0.03137255],
                [0.04313726, 0.04313726],
            ]
            per_channel_affine_qint8_zp = [
                [-128, -43],
                [-15, -128],
                [-26, -128],
                [-35, -58],
            ]
            per_channel_affine_float_qparams_ref_scales = [
                [0.0196, 0.0471],
                [0.0353, 0.0196],
                [0.0392, 0.0235],
                [0.0431, 0.0431],
            ]
            per_channel_affine_quint8_zp = [[0, 85], [113, 0], [102, 0], [93, 70]]

            self.assertEqual(myobs.min_val, ref_min_vals[ch_axis])
            self.assertEqual(myobs.max_val, ref_max_vals[ch_axis])
            if qscheme == torch.per_channel_symmetric:
                ref_scales = per_channel_symmetric_ref_scales[ch_axis]
                ref_zero_points = [0, 0] if qdtype is torch.qint8 else [128, 128]
            elif qscheme == torch.per_channel_affine_float_qparams:
                ref_scales = per_channel_affine_float_qparams_ref_scales[ch_axis]
                ref_zero_points = [-1 * ref_min_vals[ch_axis][i] / ref_scales[i] for i in range(len(ref_scales))]
            else:
                ref_scales = per_channel_affine_ref_scales[ch_axis]
                ref_zero_points = (
                    per_channel_affine_qint8_zp[ch_axis]
                    if qdtype is torch.qint8
                    else per_channel_affine_quint8_zp[ch_axis]
                )

            if reduce_range:
                ref_scales = [s * 255 / 127 for s in ref_scales]
                ref_zero_points = [math.floor(z / 2) for z in ref_zero_points]
            self.assertEqual(qparams[0], torch.tensor(ref_scales, dtype=qparams[0].dtype), rtol=1e-5, atol=0.0001)
            if qscheme == torch.per_channel_affine_float_qparams:
                self.assertEqual(qparams[1], torch.tensor(ref_zero_points, dtype=qparams[1].dtype), rtol=1e-5, atol=1)
            else:
                self.assertEqual(qparams[1], torch.tensor(ref_zero_points, dtype=qparams[1].dtype))


            # Test for serializability
            state_dict = myobs.state_dict()
            b = io.BytesIO()
            torch.save(state_dict, b)
            b.seek(0)
            loaded_dict = torch.load(b)
            for key in state_dict:
                self.assertEqual(state_dict[key], loaded_dict[key])
            loaded_obs = PerChannelMinMaxObserver(reduce_range=reduce_range, ch_axis=ch_axis, dtype=qdtype, qscheme=qscheme)
            loaded_obs.load_state_dict(loaded_dict)
            loaded_qparams = loaded_obs.calculate_qparams()
            self.assertEqual(myobs.min_val, loaded_obs.min_val)
            self.assertEqual(myobs.max_val, loaded_obs.max_val)
            self.assertEqual(myobs.calculate_qparams(), loaded_obs.calculate_qparams())