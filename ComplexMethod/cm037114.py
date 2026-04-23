def __init__(
        self,
        compile_prefix: str = "",
        is_encoder: bool = False,
    ) -> None:
        self.compiled = False
        self._compile_prefix = compile_prefix
        self._is_encoder = is_encoder

        vllm_config = get_current_vllm_config()
        self.vllm_config = vllm_config
        mode = vllm_config.compilation_config.mode
        self.layerwise_nvtx_tracing_enabled = (
            vllm_config.observability_config.enable_layerwise_nvtx_tracing
        )
        if mode is None:
            raise RuntimeError("Compilation mode cannot be NO_COMPILATION")

        backend = vllm_config.compilation_config.init_backend(
            vllm_config, prefix=compile_prefix, is_encoder=is_encoder
        )
        options = {}

        if isinstance(backend, str) and backend == "inductor":
            options = vllm_config.compilation_config.inductor_compile_config

        self.first_compile = True
        self.evaluate_guards = (
            vllm_config.compilation_config.dynamic_shapes_config.evaluate_guards
        )

        ds_type = vllm_config.compilation_config.dynamic_shapes_config.type

        if mode != CompilationMode.STOCK_TORCH_COMPILE:
            # Drop all the guards.
            if self.evaluate_guards:
                assert not envs.VLLM_USE_BYTECODE_HOOK, (
                    "compilation_config.dynamic_shapes_config.evaluate_guards "
                    "requires VLLM_USE_BYTECODE_HOOK=0. "
                )

                options["guard_filter_fn"] = lambda x: [
                    entry.guard_type == "SHAPE_ENV" for entry in x
                ]
            else:
                if hasattr(torch.compiler, "skip_all_guards_unsafe"):
                    # Torch 2.10+ provides skip_all_guards_unsafe
                    options["guard_filter_fn"] = torch.compiler.skip_all_guards_unsafe
                else:
                    # Equivalent fallback for older PyTorch: skip all guards
                    options["guard_filter_fn"] = lambda x: [False for _ in x]

        compiled_ptr: Any = self.forward
        # Validate that unbacked dynamic shapes require VLLM_USE_BYTECODE_HOOK=False

        if ds_type == DynamicShapesType.UNBACKED:
            # reason is that bytecode does torch._dynamo.eval_frame.
            # remove_from_cache(self.original_code_object()) to force a new
            # re-compilation. And if we use
            # compiled_ptr = self.check_invariants_and_forward
            # it will reset all entries.
            assert not envs.VLLM_USE_BYTECODE_HOOK, (
                "UNBACKED dynamic shapes requires VLLM_USE_BYTECODE_HOOK=0. "
            )
            assert not self.evaluate_guards, "UNBACKED dynamic shapes do not add guards"

            compiled_ptr = self.check_invariants_and_forward

        # Apply the constrain_to_fx_strides patch before first compilation.
        # This covers STOCK_TORCH_COMPILE and DYNAMO_ONCE paths. The VLLM
        # compile paths call this from their own compile() methods too.
        from vllm.env_override import _apply_constrain_to_fx_strides_patch

        _apply_constrain_to_fx_strides_patch()

        aot_context = nullcontext()
        if envs.VLLM_USE_AOT_COMPILE:
            if hasattr(torch._dynamo.config, "enable_aot_compile"):
                aot_context = torch._dynamo.config.patch(enable_aot_compile=True)
            else:
                msg = "torch._dynamo.config.enable_aot_compile is not "
                msg += "available. AOT compile is disabled and please "
                msg += "upgrade PyTorch version to use AOT compile."
                logger.warning(msg)

        with aot_context:
            self._compiled_callable = torch.compile(
                compiled_ptr,
                fullgraph=True,
                dynamic=False,
                backend=backend,
                options=options,
            )

        if envs.VLLM_USE_BYTECODE_HOOK and mode != CompilationMode.STOCK_TORCH_COMPILE:
            torch._dynamo.convert_frame.register_bytecode_hook(self.bytecode_hook)
            self._compiled_bytecode: CodeType | None = None