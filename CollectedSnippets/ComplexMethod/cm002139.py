def infer_name(self, compact: bool = True) -> str:
        """Infer a human-readable name for the benchmark config, either compact or verbose."""
        if compact:
            iter_str = f"w{self.warmup_iterations}_i{self.measurement_iterations}"
            gpu_monitor_str = "monitored" if self.gpu_monitoring else "unmonitored"
            dimensions_str = f"b{self.batch_size}_s{self.sequence_length}_n{self.num_tokens_to_generate}"
            attn_code = self.attn_implementation
            compile_str = f"compiled_{self.compile_config.mode}" if self.compile_config is not None else "uncompiled"
            kernelize_str = "kernelized" if self.kernelize else "unkernelized"
            continuous_batching_str = "cb" if self.continuous_batching else "generate"
            tp_str = "tp" if self.tp_plan is not None else "no_tp"
            sep = "-"
        else:
            iter_str = f"{self.warmup_iterations} warmup, {self.measurement_iterations} iterations"
            gpu_monitor_str = ("with" if self.gpu_monitoring else "no") + " GPU monitoring"
            dimensions_str = f"batch size {self.batch_size}, sequence length {self.sequence_length}, {self.num_tokens_to_generate} generated tokens"
            attn_code = f"{self.attn_implementation} attention"
            compile_str = "compiled" if self.compile_config is not None else "not compiled"
            kernelize_str = "kernelized" if self.kernelize else "not kernelized"
            continuous_batching_str = "continuous batching" if self.continuous_batching else "regular generate"
            if self.tp_plan is None:
                tp_str = "no_tp"
            else:
                tp_str = "tp_custom" if isinstance(self.tp_plan, dict) else "tp_auto"
            sep = ", "
        return sep.join(
            [
                iter_str,
                gpu_monitor_str,
                dimensions_str,
                attn_code,
                compile_str,
                kernelize_str,
                continuous_batching_str,
                tp_str,
            ]
        )