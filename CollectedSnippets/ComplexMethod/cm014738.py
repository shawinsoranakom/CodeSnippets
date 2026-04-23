def test_upsamplingBiMode2d_nonsupported_dtypes(self, device, antialias, num_channels, mode, dtype):
        x = torch.ones(1, num_channels, 32, 32, dtype=dtype, device=device)

        should_raise_runtime_error = True

        if "nearest" in mode:
            if antialias:
                raise SkipTest("Nearest mode does not have antialiasing")
            if dtype in (torch.uint8, ) + floating_types():
                should_raise_runtime_error = False

        elif mode == "lanczos":
            if torch.device(device).type != "cpu":
                raise SkipTest("Lanczos mode is only supported on CPU")
            if not antialias:
                raise SkipTest("Lanczos mode requires antialias=True")
            if dtype in floating_types() or (device == "cpu" and dtype == torch.uint8):
                should_raise_runtime_error = False

        elif mode in ("bilinear", "bicubic"):
            if dtype in floating_types() or (device == "cpu" and dtype == torch.uint8):
                should_raise_runtime_error = False

        if should_raise_runtime_error:
            with self.assertRaisesRegex(RuntimeError, "not implemented for"):
                F.interpolate(x, (12, 12), mode=mode, antialias=antialias)
        else:
            _ = F.interpolate(x, (12, 12), mode=mode, antialias=antialias)