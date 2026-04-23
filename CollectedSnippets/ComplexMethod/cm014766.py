def test_like_value(self, func, device):
        dtype = torch.float32 if func is not torch.randint_like else torch.int32
        for nt in _sample_njts(device=device, dtype=dtype):
            extra_kwarg_sets = [{}]
            if func is torch.full_like:
                extra_kwarg_sets = [{"fill_value": 4.2}]
            elif func is torch.randint_like:
                extra_kwarg_sets = [{"high": 5}, {"low": 4, "high": 9}]

            # only test changing dtype / device from CUDA -> CPU because CUDA might not be
            # available when running this test for CPU
            change_dtype_device_settings = (
                [False, True] if "cuda" in device else [False]
            )
            for change_dtype_device in change_dtype_device_settings:
                if change_dtype_device:
                    new_dtype = (
                        torch.float64 if func is not torch.randint_like else torch.int64
                    )
                    new_device = "cpu" if "cuda" in device else device
                    new_layout = torch.strided
                    for extra_kwargs in extra_kwarg_sets:
                        extra_kwargs.update(
                            {
                                "dtype": new_dtype,
                                "device": new_device,
                                "layout": new_layout,
                            }
                        )

                for extra_kwargs in extra_kwarg_sets:
                    nt_like = func(nt, **extra_kwargs)
                    self.assertEqual(nt.shape, nt_like.shape)
                    if change_dtype_device:
                        self.assertNotEqual(nt.device, nt_like.device)
                        self.assertNotEqual(nt.device, nt_like.dtype)
                        # layout should be ignored since only torch.jagged is supported
                        self.assertEqual(torch.jagged, nt_like.layout)
                    else:
                        self.assertEqual(nt.device, nt_like.device)
                        self.assertEqual(nt.dtype, nt_like.dtype)
                        self.assertEqual(nt.layout, nt_like.layout)
                        self.assertEqual(nt.layout, torch.jagged)

                    # don't bother trying to compare random or empty values
                    if func not in [
                        torch.empty_like,
                        torch.rand_like,
                        torch.randn_like,
                        torch.randint_like,
                    ]:
                        for nt_ub in nt_like.unbind():
                            t_like = func(nt_ub, **extra_kwargs)
                            self.assertEqual(nt_ub, t_like)