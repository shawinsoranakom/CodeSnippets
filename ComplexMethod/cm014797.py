def _test_pow(self, base, exponent, np_exponent=None):
        if np_exponent is None:
            np_exponent = exponent

        def to_np(value):
            if isinstance(value, torch.Tensor):
                return value.cpu().numpy()
            return value

        try:
            np_res = np.power(to_np(base), to_np(np_exponent))
            expected = (
                torch.from_numpy(np_res)
                if isinstance(np_res, np.ndarray)
                else torch.tensor(np_res, dtype=base.dtype)
            )
        except ValueError as e:
            err_msg = "Integers to negative integer powers are not allowed."
            self.assertEqual(str(e), err_msg)
            out = torch.empty_like(base)
            test_cases = [
                lambda: base.pow(exponent),
                lambda: base.pow_(exponent),
                lambda: torch.pow(base, exponent),
                lambda: torch.pow(base, exponent, out=out),
            ]
            for test_case in test_cases:
                self.assertRaisesRegex(RuntimeError, err_msg, test_case)
        else:
            if isinstance(base, torch.Tensor):
                actual = base.pow(exponent)
                self.assertEqual(actual, expected.to(actual))
                actual = base.clone()
                # When base is a 0-dim cpu tensor and exp is a cuda tensor, we exp `pow` to work but `pow_` to fail, since
                # `pow` will try to create the output tensor on a cuda device, but `pow_` needs to use the cpu tensor as the output
                if (
                    isinstance(exponent, torch.Tensor)
                    and base.dim() == 0
                    and base.device.type == "cpu"
                    and exponent.device.type in ["cuda", "xpu"]
                ):
                    regex = (
                        f"Expected all tensors to be on the same device, "
                        f"but found at least two devices, {device_type}.* and cpu!"
                    )
                    self.assertRaisesRegex(RuntimeError, regex, base.pow_, exponent)
                elif torch.can_cast(torch.result_type(base, exponent), base.dtype):
                    actual2 = actual.pow_(exponent)
                    self.assertEqual(actual, expected.to(actual))
                    self.assertEqual(actual2, expected.to(actual2))
                else:
                    self.assertRaisesRegex(
                        RuntimeError,
                        r"result type \w+ can't be cast to the desired output type \w+",
                        lambda: actual.pow_(exponent),
                    )

            actual = torch.pow(base, exponent)
            self.assertEqual(actual, expected.to(actual))

            actual2 = torch.pow(base, exponent, out=actual)
            self.assertEqual(actual, expected.to(actual))
            self.assertEqual(actual2, expected.to(actual))