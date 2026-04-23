def test_histogram_observer(self, qdtype, qscheme, reduce_range):
        myobs = HistogramObserver(bins=3, dtype=qdtype, qscheme=qscheme, reduce_range=reduce_range)
        # Calculate qparams should work for empty observers
        qparams = myobs.calculate_qparams()
        x = torch.tensor([2.0, 3.0, 4.0, 5.0], requires_grad=True)
        y = torch.tensor([5.0, 6.0, 7.0, 8.0])
        out_x = myobs(x)
        self.assertTrue(out_x.requires_grad)
        myobs(y)
        self.assertEqual(myobs.min_val, 2.0)
        self.assertEqual(myobs.max_val, 8.0)
        self.assertEqual(myobs.histogram, [2., 3., 3.])

        qparams = myobs.calculate_qparams()

        if reduce_range:
            if qscheme == torch.per_tensor_symmetric:
                ref_scale = 0.0470588 * 255 / 127
                ref_zero_point = 0 if qdtype is torch.qint8 else 128
            else:
                ref_scale = 0.0235294 * 255 / 127
                ref_zero_point = -64 if qdtype is torch.qint8 else 0
        else:
            if qscheme == torch.per_tensor_symmetric:
                ref_scale = 0.0470588
                ref_zero_point = 0 if qdtype is torch.qint8 else 128
            else:
                ref_scale = 0.0235294
                ref_zero_point = -128 if qdtype is torch.qint8 else 0

        self.assertEqual(qparams[1].item(), ref_zero_point)
        self.assertEqual(qparams[0].item(), ref_scale, atol=1e-5, rtol=0)
        # Test for serializability
        state_dict = myobs.state_dict()
        b = io.BytesIO()
        torch.save(state_dict, b)
        b.seek(0)
        loaded_dict = torch.load(b)
        for key in state_dict:
            self.assertEqual(state_dict[key], loaded_dict[key])
        loaded_obs = HistogramObserver(bins=3, dtype=qdtype, qscheme=qscheme, reduce_range=reduce_range)
        loaded_obs.load_state_dict(loaded_dict)
        loaded_qparams = loaded_obs.calculate_qparams()
        self.assertEqual(myobs.min_val, loaded_obs.min_val)
        self.assertEqual(myobs.max_val, loaded_obs.max_val)
        self.assertEqual(myobs.histogram, loaded_obs.histogram)
        self.assertEqual(myobs.bins, loaded_obs.bins)
        self.assertEqual(myobs.calculate_qparams(), loaded_obs.calculate_qparams())