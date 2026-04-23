def __init__(
        self,
        hidden_size: int,
        eps: float = 1e-6,
        var_hidden_size: int | None = None,
        has_weight: bool = True,
        dtype: torch.dtype | None = None,
    ) -> None:
        super().__init__()

        self.hidden_size = hidden_size
        self.variance_epsilon = eps
        self.variance_size_override = (
            None if var_hidden_size == hidden_size else var_hidden_size
        )
        weight_dtype = dtype or torch.get_default_dtype()
        self.has_weight = has_weight
        self.weight = torch.ones(hidden_size, dtype=weight_dtype)
        if self.has_weight:
            self.weight = nn.Parameter(self.weight)

        if current_platform.is_rocm():
            aiter_rmsnorm_enabled = rocm_aiter_ops.is_rmsnorm_enabled()
            self.rocm_norm_func_with_add = dispatch_rocm_rmsnorm_func(
                dtype=weight_dtype, use_aiter=aiter_rmsnorm_enabled
            )

        # Optional: enable Oink Blackwell RMSNorm custom-op fast path on
        # compatible CUDA devices (e.g., SM100) when the external Oink
        # package is available. This is detected once at construction time
        # to avoid per-call device queries in the hot path.
        self._use_oink_fused_add_rmsnorm = False
        if (
            not current_platform.is_rocm()
            and torch.cuda.is_available()
            and bool(getattr(envs, "VLLM_USE_OINK_OPS", False))
        ):
            # NOTE: vLLM disables custom ops by default when using Inductor.
            # If this op is disabled, CustomOp will dispatch to forward_native,
            # and the Oink path in forward_cuda will never run.
            if getattr(self._forward_method, "__func__", None) is getattr(
                self.forward_native, "__func__", None
            ):
                try:
                    from vllm.config import get_cached_compilation_config

                    custom_ops = get_cached_compilation_config().custom_ops
                except Exception:
                    custom_ops = ["<unknown>"]
                logger.warning_once(
                    "VLLM_USE_OINK_OPS=1 but the `rms_norm` custom op is "
                    "disabled (CompilationConfig.custom_ops=%s). Enable it via "
                    "`compilation_config={'custom_ops': ['none', '+rms_norm']}` "
                    "(or `['all']`) to let vLLM call into torch.ops.oink.*.",
                    custom_ops,
                )
                # Custom op disabled => forward_cuda won't run. Avoid doing any
                # external Oink initialization work in this case.
            else:
                try:
                    device_index = torch.accelerator.current_device_index()
                    if _oink_ops.is_oink_available_for_device(device_index):
                        self._use_oink_fused_add_rmsnorm = (
                            _oink_ops.has_fused_add_rms_norm()
                        )
                except Exception as e:
                    # If anything goes wrong (no Oink install, CPU-only env, etc.),
                    # silently fall back to the built-in RMSNorm path.
                    logger.warning_once(
                        "VLLM_USE_OINK_OPS=1 but failed to initialize Oink "
                        "RMSNorm; falling back to vLLM RMSNorm. Error: %s",
                        e,
                    )
                    self._use_oink_fused_add_rmsnorm = False