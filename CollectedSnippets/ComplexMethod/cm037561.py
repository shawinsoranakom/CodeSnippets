def dispatch_forward(self, compile_native: bool):
        # NOTE(woosuk): Here we assume that vLLM was built for only one
        # specific backend. Currently, we do not support dynamic dispatching.
        compilation_config = get_cached_compilation_config()

        # NOTE(shen-shanshan): CustomOp object can be enforce enabled, e.g.,
        # enable device-specific kernels in ViT models when enabling graph
        # mode. By default, it will follow the compilation_config to determine
        # whether enable itself.
        # This enforce_enable mechanism will be removed after we adding a
        # separate compilation_config for multi-modal part.
        enabled = self._enforce_enable or self.enabled()
        if enabled:
            compilation_config.enabled_custom_ops.update([self.__class__.name])
        else:
            compilation_config.disabled_custom_ops.update([self.__class__.name])

        if not enabled:
            # Compile forward_native to avoid eager torch ops if inside
            # opaque torch custom op (e.g. fused_moe, unified_attention, etc.)
            return self.maybe_compile(self.forward_native, enable=compile_native)

        if current_platform.is_rocm():
            return self.forward_hip
        elif current_platform.is_cpu():
            return self.forward_cpu
        elif current_platform.is_tpu():
            return self.forward_tpu
        elif current_platform.is_xpu():
            return self.forward_xpu
        elif current_platform.is_out_of_tree():
            return self.forward_oot
        else:
            return self.forward_cuda