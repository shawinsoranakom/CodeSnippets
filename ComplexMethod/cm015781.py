def _interpolate_tests(self, is_upsample):
        # - cubic mode is not supported for opsets below 11;
        # - linear mode does not match for opsets below 11;
        modes = ["nearest", "linear", "bicubic"]
        if self.opset_version < 11:
            modes = ["nearest"]
        x = [
            torch.randn(1, 2, 6, requires_grad=True),
            torch.randn(1, 2, 4, 6, requires_grad=True),
            torch.randn(1, 2, 4, 4, 6, requires_grad=True),
        ]

        for mode in modes:
            for xi in x:
                mode_i = mode
                # TODO: enable bicubic downsample when ORT precision loss fixed
                if mode == "bicubic" and xi.dim() != 4:
                    continue
                elif mode == "linear":
                    if xi.dim() == 3:
                        # TODO : enable when linear mode is implemented for 1d inputs in ORT
                        continue
                    elif xi.dim() == 4:
                        mode_i = "bilinear"
                    elif xi.dim() == 5:
                        # TODO : enable when linear mode is implemented for 3d inputs in ORT
                        mode_i = "trilinear"
                        continue
                self._interpolate(xi, mode_i, True, is_upsample)
                # test with align_corners if supported
                if mode != "nearest":
                    self._interpolate(xi, mode_i, True, is_upsample, True)
                # the following cases, require dynamic sizes/scales,
                # which which is not supported for opset_version < 9
                if self.opset_version >= 9:
                    self._interpolate(xi, mode_i, True, is_upsample)
                    # test with align_corners if supported
                    if mode != "nearest":
                        self._interpolate(xi, mode_i, False, is_upsample, True)
                    self._interpolate(xi, mode_i, False, is_upsample)