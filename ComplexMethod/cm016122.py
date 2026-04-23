def get_tolerance_and_cosine_flag(self, is_training, current_device, name):
        tolerance = 1e-4
        cosine = self.args.cosine
        # Increase the tolerance for torch allclose
        if self.args.float16 or self.args.amp:
            if self.args.freezing and (freezing := self._tolerance["freezing"]):
                higher_fp16 = freezing.get("higher_fp16", None)
                even_higher = freezing.get("even_higher", None)
                if higher_fp16 and name in higher_fp16:
                    return 1e-2, cosine
                elif even_higher and name in even_higher:
                    return 8 * 1e-2, cosine
            if name in self._tolerance["higher_fp16"]:
                return 1e-2, cosine
            elif name in self._tolerance["even_higher"]:
                return 8 * 1e-2, cosine
            return 1e-3, cosine

        if self.args.bfloat16:
            if name in self._tolerance["higher_bf16"]:
                return 1e-2, cosine
            elif current_device == "xpu" and name in self._tolerance["higher_bf16_xpu"]:
                return 8 * 1e-2, cosine

        if is_training and (current_device == "cuda" or current_device == "xpu"):
            tolerance = 1e-3
            if name in self._tolerance["cosine"]:
                cosine = True
            elif name in self._tolerance["higher"]:
                tolerance = 1e-3
            elif name in self._tolerance["even_higher"]:
                tolerance = 8 * 1e-2
        return tolerance, cosine