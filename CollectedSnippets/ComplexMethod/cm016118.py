def get_tolerance_and_cosine_flag(self, is_training, current_device, name):
        cosine = self.args.cosine
        tolerance = 1e-3

        if self.args.freezing and name in self._tolerance["freezing"]:
            # the conv-batchnorm fusion used under freezing may cause relatively
            # large numerical difference. We need a larger tolerance.
            # Check https://github.com/pytorch/pytorch/issues/120545 for context
            tolerance = 8 * 1e-2

        if is_training:
            from torch._inductor import config as inductor_config

            if name in self._tolerance["highest_training"]:
                tolerance = 16 * 1e-2
            elif name in self._tolerance["even_higher"] or (
                inductor_config.max_autotune
                and name in self._tolerance["even_higher_max_autotune"]
            ):
                tolerance = 8 * 1e-2
            elif name in self._tolerance["higher_training"] or (
                self.args.amp and name in self._tolerance["higher_amp"]
            ):
                tolerance = 4 * 1e-2
            elif (
                name in self._tolerance["higher_fp16_xpu"]
                and self.args.float16
                and current_device == "xpu"
            ):
                tolerance = 4 * 1e-2
            else:
                tolerance = 1e-2
        return tolerance, cosine