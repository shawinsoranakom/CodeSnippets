def test_exp(self, device, dtype):
        for v in (2, -2) + ((1j, 1 + 1j) if dtype.is_complex else ()):
            a = (
                torch.tensor(v, dtype=dtype, device=device)
                * torch.arange(18, device=device)
                / 3
                * math.pi
            )
            a = a.to(dtype)
            # bfloat16 overflows
            if dtype == torch.bfloat16:
                return
            self.compare_with_numpy(torch.exp, np.exp, a)

            if dtype.is_complex:
                inf_real_zero_imag_in = torch.tensor(
                    complex(float("inf"), 0), device=device, dtype=dtype
                )
                inf_real_zero_imag_out = torch.exp(inf_real_zero_imag_in).item()
                self.assertTrue(math.isinf(inf_real_zero_imag_out.real))
                if self.device_type == "cpu":
                    pass
                    # These are commented out because it cannot be consistently reproduced.
                    # This is incorrect. It should be zero. Need fix!
                    # https://github.com/pytorch/pytorch/issues/40590
                    # self.assertNotEqual(inf_real_zero_imag_out.imag, 0)
                    # This is incorrect. They should equal. Need fix!
                    # https://github.com/pytorch/pytorch/issues/40590
                    # with self.assertRaises(AssertionError):
                    #     self.compare_with_numpy(torch.exp, np.exp, inf_real_zero_imag_in)
                else:
                    self.assertEqual(inf_real_zero_imag_out.imag, 0, atol=0, rtol=0)
                    self.compare_with_numpy(torch.exp, np.exp, inf_real_zero_imag_in)

                zero_real_inf_imag_in = torch.tensor(
                    complex(0, float("inf")), device=device, dtype=dtype
                )
                zero_real_inf_imag_out = torch.exp(zero_real_inf_imag_in).item()
                self.assertTrue(math.isnan(zero_real_inf_imag_out.real))
                self.assertTrue(math.isnan(zero_real_inf_imag_out.imag))
                # Ensure we are notified when NumPy changes its behavior
                self.compare_with_numpy(torch.exp, np.exp, zero_real_inf_imag_in)

                inf_real_imag_in = torch.tensor(
                    complex(float("inf"), float("inf")), device=device, dtype=dtype
                )
                inf_real_imag_out = torch.exp(inf_real_imag_in).item()
                if self.device_type == "cpu":
                    pass
                    # This is incorrect. Need fix! https://github.com/pytorch/pytorch/issues/40590
                    # This is commented out because it cannot be consistently reproduced.
                    # with self.assertRaises(AssertionError):
                    #     self.compare_with_numpy(torch.exp, np.exp, inf_real_imag_in)
                else:
                    self.assertTrue(math.isinf(inf_real_imag_out.real))
                    self.assertTrue(math.isnan(inf_real_imag_out.imag))
                    self.compare_with_numpy(torch.exp, np.exp, inf_real_imag_in)

                inf_real_nan_imag_in = torch.tensor(
                    complex(float("inf"), float("nan")), device=device, dtype=dtype
                )
                inf_real_nan_imag_out = torch.exp(inf_real_nan_imag_in).item()
                if self.device_type == "cpu":
                    pass
                    # This is incorrect. It should be inf. Need fix! https://github.com/pytorch/pytorch/issues/40590
                    # This is commented out because it cannot be consistently reproduced.
                    # with self.assertRaises(AssertionError):
                    #     self.compare_with_numpy(torch.exp, np.exp, inf_real_nan_imag_in)
                else:
                    self.assertTrue(math.isinf(inf_real_nan_imag_out.real))
                    self.assertTrue(math.isnan(inf_real_nan_imag_out.imag))
                    self.compare_with_numpy(torch.exp, np.exp, inf_real_nan_imag_in)

                nan_real_inf_imag_in = torch.tensor(
                    complex(float("nan"), float("inf")), device=device, dtype=dtype
                )
                nan_real_inf_imag_out = torch.exp(nan_real_inf_imag_in).item()
                self.assertTrue(math.isnan(nan_real_inf_imag_out.real))
                self.assertTrue(math.isnan(nan_real_inf_imag_out.imag))
                # Ensure we are notified when NumPy changes its behavior
                self.compare_with_numpy(torch.exp, np.exp, nan_real_inf_imag_in)