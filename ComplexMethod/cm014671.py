def test_float8_basics_layout_permutations(self, device) -> None:
        if not _device_supports_scaled_mm_fp8(device):
            raise unittest.SkipTest(f8_msg)
        if torch.cuda.is_available():
            for (x_cm, y_cm) in itertools.product([True, False], repeat=2):
                # SM 10 and 11 support all permutations, SM 12 TT and TN, SM 9 only TN
                major, minor = torch.cuda.get_device_capability(0)
                if major in (10, 11):
                    layouts_supported = True
                elif major == 12 and (minor == 1 or _get_torch_cuda_version() >= (13, 1)):
                    layouts_supported = x_cm
                else:
                    layouts_supported = (x_cm, y_cm) == (True, False)
                with contextlib.nullcontext() if layouts_supported else self.assertRaises(RuntimeError):
                    self._test_tautological_mm(device, size=64, out_dtype=torch.bfloat16, x_cm=x_cm, y_cm=y_cm)