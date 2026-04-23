def dtype_policy(self, value):
        policy = dtype_policies.get(value)
        if isinstance(self._dtype_policy, DTypePolicyMap) and self.path:
            if self.path in self._dtype_policy:
                del self._dtype_policy[self.path]
            self._dtype_policy[self.path] = policy
        else:
            self._dtype_policy = policy
        if policy.quantization_mode is not None:
            if self.built and not getattr(self, "_is_quantized", False):
                if policy.quantization_mode == "gptq":
                    raise ValueError(
                        "Implicitly enabling GPTQ quantization by setting "
                        f"`dtype_policy` to '{value}' is not supported. "
                        "GPTQ requires a calibration dataset and a "
                        "`GPTQConfig` object.\n\n"
                        "Please use the `.quantize('gptq', config=...)` method "
                        "on the layer or model instead."
                    )
                self.quantize(policy.quantization_mode)