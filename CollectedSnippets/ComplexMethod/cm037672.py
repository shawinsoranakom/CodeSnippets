def __init__(
        self,
        weight_config: dict[str, Any],
        input_config: dict[str, Any] | None,
        moe: FusedMoEConfig,
    ):
        super().__init__(moe)
        self.weight_quant = weight_config
        self.input_quant = input_config

        weight_qscheme = self.weight_quant.get("qscheme")
        if not weight_qscheme == "per_group":
            raise ValueError(
                "For MX(FP4) Fused MoE layers, only per-group scales "
                f"for weights are supported. Found {weight_qscheme}."
            )  # noqa E501

        self.weight_dtype = self.weight_quant["dtype"].replace("fp", "mxfp")
        if self.input_quant is not None:
            input_quant = self.input_quant["dtype"]
            if input_quant in ["fp4", "fp6_e3m2", "fp6_e2m3"]:
                self.input_dtype = input_quant.replace("fp", "mxfp")
            elif input_quant == "fp8_e4m3":
                self.input_dtype = input_quant.replace("fp8_e4m3", "fp8")
            else:
                raise NotImplementedError(
                    f"Current input dtype {input_quant} is not compatible \
                        with OCP MX (weight) MoE quantization. Please open an issue"
                )
        else:
            self.input_dtype = None

        self.fp4_dtype = getattr(torch, "float4_e2m1fn_x2", None)

        self.ocp_mx_scheme = OCP_MX_Scheme.from_quant_dtype(
            self.input_dtype, self.weight_dtype
        )

        if self.ocp_mx_scheme is None:
            raise ValueError(
                f"Unsupported OCP MX dtype combination for MoE: "
                f"input_dtype={self.input_dtype}, weight_dtype={self.weight_dtype}. "
                f"Please check that the combination is supported in OCP_MX_Scheme."
            )

        # TODO(bowenbao): refactor and introduce backends for other OCP MX schemes,
        # use kernel abstraction for all OCP MX MOE implementations.
        self.mxfp4_backend: Mxfp4MoeBackend = Mxfp4MoeBackend.NONE
        self.experts_cls: type[mk.FusedMoEExperts] | None = None
        self.moe_kernel: mk.FusedMoEKernel | None = None

        # Used for triton kernel precision configs
        self.w13_precision_config = None
        self.w2_precision_config = None

        if self.input_quant is not None:
            self.static_input_scales = not self.input_quant.get("is_dynamic")
        else:
            self.static_input_scales = False

        if any(
            self.ocp_mx_scheme.endswith(a_scheme)
            for a_scheme in ["a_mxfp4", "a_mxfp6_e3m2", "a_mxfp6_e2m3"]
        ):
            if self.static_input_scales:
                raise NotImplementedError(
                    "QuarkOCP_MX_MoEMethod with static input scales is currently "
                    f"not implemented for OCP MX scheme {self.ocp_mx_scheme}. "
                    "Please open an issue."
                )
        elif self.ocp_mx_scheme.endswith("a_fp8") and not self.static_input_scales:
            raise NotImplementedError(
                "QuarkOCP_MX_MoEMethod with dynamic input scales is currently "
                f"not implemented for OCP MX scheme {self.ocp_mx_scheme}. "
                "Please open an issue."
            )

        self.use_rocm_aiter_moe = rocm_aiter_ops.is_fused_moe_enabled()

        self.model_type = getattr(
            get_current_vllm_config().model_config.hf_config, "model_type", None
        )

        self.emulate = (
            not current_platform.supports_mx()
            or not self.ocp_mx_scheme.startswith("w_mxfp4")
        ) and (
            self.mxfp4_backend is Mxfp4MoeBackend.NONE or not self.use_rocm_aiter_moe
        )

        if self.ocp_mx_scheme == "w_mxfp4":
            self.mxfp4_backend, self.experts_cls = select_gpt_oss_mxfp4_moe_backend(moe)

        if self.emulate:
            # We use the same code path between MXFP4/MXFP6 emulation.
            self.mxfp4_backend = Mxfp4MoeBackend.EMULATION

        # TODO: Remove `self.mxfp4_backend != Mxfp4MoeBackend.NONE` and make it so that
        # all MXFP4 backends use the kernel abstraction.
        if self.mxfp4_backend != Mxfp4MoeBackend.NONE:
            self.experts_cls = backend_to_kernel_cls(self.mxfp4_backend)[0]

        if self.emulate:
            logger.warning_once(
                f"The current mode (supports_mx={current_platform.supports_mx()}, "
                f"use_rocm_aiter_moe={self.use_rocm_aiter_moe}, "
                f"ocp_mx_scheme={self.ocp_mx_scheme}) "
                "does not support native MXFP4/MXFP6 "
                "computation. Simulated weight dequantization and activation "
                "QDQ (quantize and dequantize) will be used, with the linear "
                "layers computed in high precision."
            )
        else:
            logger.warning_once(
                "The current mode supports native MoE MXFP4 computation"
            )