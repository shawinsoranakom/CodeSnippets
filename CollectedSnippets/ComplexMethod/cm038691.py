def __post_init__(self) -> None:
        count_none = self.custom_ops.count("none")
        count_all = self.custom_ops.count("all")
        assert count_none + count_all <= 1, "Can only specify 'none' or 'all'"

        # TODO(zou3519/luka): There are 2 issues with auto-functionalization V2:
        # 1. A bug in PyTorch, fixed in 2.7:
        #    https://github.com/pytorch/pytorch/issues/147924
        # 2. Custom passes (fusion) rely on auto-functionalization V1 and don't
        #    work with V2. Addressing this will take extra engineering effort
        #    and it is not yet a priority. RFC here:
        #    https://github.com/vllm-project/vllm/issues/14703

        KEY = "enable_auto_functionalized_v2"
        if KEY not in self.inductor_compile_config:
            self.inductor_compile_config[KEY] = False

        # Tie inductor runtime assertions to debug logging mode.
        # These assertions add ~2ms overhead per forward pass on large
        # models (e.g., DeepSeek-R1 671B: ~340 assert_size_stride + ~60
        # assert_alignment calls per forward). PyTorch >= 2.12 has a
        # native fix (assert-once), so we only apply this workaround on
        # older versions. On torch < 2.12, enable asserts only when
        # VLLM_LOGGING_LEVEL=DEBUG. Users can still override explicitly
        # via --compilation-config '{"inductor_compile_config":
        # {"size_asserts": true, ...}}'.
        # See: https://github.com/pytorch/pytorch/issues/177719
        if not is_torch_equal_or_newer("2.12.0.dev"):
            enable_asserts = envs.VLLM_LOGGING_LEVEL == "DEBUG"
            for key in (
                "size_asserts",
                "alignment_asserts",
                "scalar_asserts",
            ):
                self.inductor_compile_config.setdefault(key, enable_asserts)

        for k, v in self.inductor_passes.items():
            if not isinstance(v, str):
                assert callable(v), f"pass {k} should be callable or a qualified name"
                self.inductor_compile_config[k] = (
                    v if isinstance(v, InductorPass) else CallableInductorPass(v)
                )
                continue

            # resolve function from qualified name
            names = v.split(".")
            module = ".".join(names[:-1])
            func_name = names[-1]
            func = __import__(module).__dict__[func_name]
            self.inductor_compile_config[k] = (
                func if isinstance(func, InductorPass) else CallableInductorPass(func)
            )

        if (
            self.pass_config.enable_qk_norm_rope_fusion
            and "+rotary_embedding" not in self.custom_ops
        ):
            # TODO(zhuhaoran): support rope native forward match and remove this.
            # Linked issue: https://github.com/vllm-project/vllm/issues/28042
            self.custom_ops.append("+rotary_embedding")
        if (
            self.pass_config.fuse_rope_kvcache
            and "+rotary_embedding" not in self.custom_ops
        ):
            # TODO(Rohan138): support rope native forward match and remove this.
            # Linked issue: https://github.com/vllm-project/vllm/issues/28042
            self.custom_ops.append("+rotary_embedding")

        if (
            is_torch_equal_or_newer("2.9.0.dev")
            and "combo_kernels" not in self.inductor_compile_config
            and "benchmark_combo_kernel" not in self.inductor_compile_config
            # (fixme @boyuan) combo kernel does not support cpu yet.
            and not current_platform.is_cpu()
        ):
            # use horizontal fusion, which is useful for fusing qk-norm and
            # qk-rope when query and key have different shapes.
            self.inductor_compile_config["combo_kernels"] = True
            self.inductor_compile_config["benchmark_combo_kernel"] = True

        if self.use_inductor_graph_partition and not is_torch_equal_or_newer(
            "2.9.0.dev"
        ):
            raise ValueError(
                "use_inductor_graph_partition is only "
                "supported with torch>=2.9.0.dev. Set "
                "use_inductor_graph_partition=False instead."
            )

        for op in self.custom_ops:
            if op[0] not in {"+", "-"} and op not in {"all", "none"}:
                raise ValueError(
                    f"Invalid syntax '{op}' for custom op, "
                    "must be 'all', 'none', '+op' or '-op' "
                    "(where 'op' is the registered op name)"
                )

        # Currently only eager and inductor backend are supported.
        # for piecewise compilation. Custom backends are not supported for
        # piecewise compilation. Update when more backends are supported.
        if self.mode == CompilationMode.VLLM_COMPILE and self.backend not in [
            "",
            "eager",
            "inductor",
        ]:
            raise ValueError(
                f"Invalid backend for piecewise compilation: {self.backend}"
            )

        # Validate encoder CUDA graph configuration
        if (
            self.cudagraph_mm_encoder
            and self.encoder_cudagraph_max_vision_items_per_batch < 0
        ):
            raise ValueError(
                "encoder_cudagraph_max_vision_items_per_batch must be "
                "non-negative (0 = auto-infer)"
            )
        if (
            self.cudagraph_mm_encoder
            and self.encoder_cudagraph_max_frames_per_batch is not None
            and self.encoder_cudagraph_max_frames_per_batch < 0
        ):
            raise ValueError(
                "encoder_cudagraph_max_frames_per_batch must be "
                "non-negative (None = auto-infer)"
            )

        if self.backend == "":
            self.backend = current_platform.get_compile_backend()