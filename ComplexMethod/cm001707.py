def _skip_if_ep_not_supported(self):
        """Check and skip test if EP is not supported for this model/environment."""
        if not is_torch_greater_or_equal("2.9"):
            self.skipTest("Expert parallel tests require torch >= 2.9")

        if torch.cuda.is_available() or torch.xpu.is_available():
            self.skipTest("Expert parallel mixin tests are CPU-only and should not run on GPU or XPU machines")

        if os.cpu_count() < self.tensor_parallel_size:
            self.skipTest(
                f"Expert parallel tests require at least {self.tensor_parallel_size} CPUs, "
                f"but only {os.cpu_count()} available"
            )

        if not hasattr(self.model_tester, "causal_lm_class") or self.model_tester.causal_lm_class is None:
            self.skipTest("Model tester does not have causal_lm_class (not using CausalLMModelTester)")

        if not self._has_ep_plan():
            self.skipTest("Model does not have an expert parallel plan (base_model_ep_plan)")