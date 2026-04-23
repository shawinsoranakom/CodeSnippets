def test_per_tensor_observers(self, qdtype, qscheme, reduce_range):
        # reduce_range cannot be true for symmetric quantization with uint8
        if (qdtype == torch.quint8 and qscheme == torch.per_tensor_symmetric) or qdtype == torch.qint32:
            reduce_range = False
        if qdtype == torch.quint4x2:
            return

        ObserverList = [MinMaxObserver(dtype=qdtype, qscheme=qscheme, reduce_range=reduce_range),
                        MovingAverageMinMaxObserver(averaging_constant=0.5,
                                                    dtype=qdtype,
                                                    qscheme=qscheme,
                                                    reduce_range=reduce_range)]

        def _get_ref_params(reduce_range, qscheme, dtype, input_scale, min_val, max_val):
            if dtype not in _INT_DTYPES:
                raise AssertionError(f"Not supported dtype: {dtype}, supported dtypes are {_INT_DTYPES}")
            eps = torch.tensor([tolerance])
            if dtype in [torch.qint8, torch.int8]:
                if reduce_range:
                    quant_min, quant_max = -64, 63
                else:
                    quant_min, quant_max = -128, 127
            elif dtype in [torch.quint8, torch.uint8]:
                if reduce_range:
                    quant_min, quant_max = 0, 127
                else:
                    quant_min, quant_max = 0, 255
            elif dtype == torch.int16:
                quant_min, quant_max = -1 * (2 ** 15), (2 ** 15) - 1
            elif dtype == torch.uint16:
                quant_min, quant_max = 0, (2 ** 16) - 1
            elif dtype in [torch.qint32, torch.int32]:
                quant_min, quant_max = -1 * (2 ** 31), (2 ** 31) - 1

            min_val_neg = torch.tensor([0.])
            max_val_pos = torch.tensor([input_scale * max_val]) if qdtype is torch.qint32 else torch.tensor([max_val])

            scale, zero_point = 1.0, 0
            if qscheme == torch.per_tensor_symmetric or qscheme == torch.per_channel_symmetric:
                scale = torch.max(-min_val_neg, max_val_pos) / (float(quant_max - quant_min) / 2)
                scale = torch.max(scale, eps)
                if dtype in [torch.quint8, torch.uint8]:
                    zero_point = 128
                if dtype == torch.uint16:
                    zero_point = 2 ** 15
            else:
                scale = torch.max((max_val_pos - min_val_neg) / float(quant_max - quant_min), eps)
                zero_point = quant_min - torch.round(min_val_neg / scale).to(torch.int)
                zero_point = torch.clamp(zero_point, quant_min, quant_max)

            return scale, zero_point

        for myobs in ObserverList:
            # Calculate Qparams should return with a warning for observers with no data
            qparams = myobs.calculate_qparams()
            input_scale = 2**16 if qdtype is torch.qint32 else 1
            if type(myobs) is MinMaxObserver:
                x = torch.tensor([1.0, 2.0, 2.0, 3.0, 4.0, 5.0, 6.0]) * input_scale
                y = torch.tensor([4.0, 5.0, 5.0, 6.0, 7.0, 8.0]) * input_scale
            else:
                # Moving average of min/max for x and y matches that of
                # extreme values for x/y used for minmax observer
                x = torch.tensor([0.0, 2.0, 2.0, 3.0, 4.0, 5.0, 6.0]) * input_scale
                y = torch.tensor([2.0, 5.0, 5.0, 6.0, 7.0, 10.0]) * input_scale

            result = myobs(x)
            result = myobs(y)
            self.assertEqual(result, y)
            self.assertEqual(myobs.min_val, 1.0 * input_scale)
            self.assertEqual(myobs.max_val, 8.0 * input_scale)
            qparams = myobs.calculate_qparams()
            ref_scale, ref_zero_point = _get_ref_params(reduce_range, qscheme, qdtype, input_scale, 1.0, 8.0)

            self.assertEqual(qparams[1].item(), ref_zero_point)
            self.assertEqual(qparams[0].item(), ref_scale, atol=1e-5, rtol=0)
            state_dict = myobs.state_dict()
            b = io.BytesIO()
            torch.save(state_dict, b)
            for weights_only in [True, False]:
                b.seek(0)
                loaded_dict = torch.load(b, weights_only=weights_only)
                for key in state_dict:
                    self.assertEqual(state_dict[key], loaded_dict[key])
                loaded_obs = MinMaxObserver(dtype=qdtype, qscheme=qscheme, reduce_range=reduce_range)
                loaded_obs.load_state_dict(loaded_dict)
                loaded_qparams = loaded_obs.calculate_qparams()
                self.assertEqual(myobs.min_val, loaded_obs.min_val)
                self.assertEqual(myobs.max_val, loaded_obs.max_val)
                self.assertEqual(myobs.calculate_qparams(), loaded_obs.calculate_qparams())