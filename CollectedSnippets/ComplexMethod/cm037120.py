def __call__(self: type[_T], *args: Any, **kwargs: Any) -> Any:
        # torch.compiler.is_compiling() means we are inside the compilation
        # e.g. TPU has the compilation logic in model runner, so we don't
        # need to compile the model inside.
        if self.do_not_compile or torch.compiler.is_compiling():
            return self.forward(*args, **kwargs)

        # If skip_compiled is set, bypass compiled model call. This is used e.g. for
        # enc-dec models where tensor shapes/types vary across invocations, preventing
        # the capture of a single computational graph.
        if is_forward_context_available() and get_forward_context().skip_compiled:
            return self.forward(*args, **kwargs)

        # if aot_compiled_fn is set, call it with partition wrapper context.
        # The partition wrapper must be active at runtime for CUDA graph
        # capture to work correctly with inductor graph partitioning.
        if getattr(self, "aot_compiled_fn", None) is not None:
            with maybe_use_cudagraph_partition_wrapper(self.vllm_config):
                return self.aot_compiled_fn(self, *args, **kwargs)

        ds_type = self.compilation_config.dynamic_shapes_config.type
        cache_dir = None
        aot_compilation_path = None
        if envs.VLLM_USE_AOT_COMPILE:
            """
            When using torch.compile in AOT mode, we store the cache artifacts
            under VLLM_CACHE_ROOT/torch_compile_cache/torch_aot_compile/{hash}
            The {hash} contains all of the factors except for the source files
            being traced through, because we don't actually know which source
            files to check at this point (before dynamo runs).
            On loading we will actually look at the source files being traced
            through. If any source file have changed (compared with the
            serialized backend artifacts), then we need to generate a new AOT
            compile artifact from scratch.
            """
            from .caching import aot_compile_hash_factors

            factors: list[str] = aot_compile_hash_factors(self.vllm_config)

            factors.append(_model_hash_key(self.forward))
            hash_key = hashlib.sha256(str(factors).encode()).hexdigest()
            cache_dir = os.path.join(
                envs.VLLM_CACHE_ROOT,
                "torch_compile_cache",
                "torch_aot_compile",
                hash_key,
            )

            # Hash-level dir; shared across ranks on the same node.
            self.compilation_config.local_cache_dir = cache_dir
            inductor_cache = os.path.join(cache_dir, "inductor_cache")
            os.makedirs(inductor_cache, exist_ok=True)
            # Process-wide: post-load execution, CUDA-graph capture, and later
            # autotune/recompile all need to write under {hash}/inductor_cache/.
            # Unconditional because torch's cache_dir() may have pre-filled the
            # /tmp default during import, making setdefault a no-op.
            os.environ["TORCHINDUCTOR_CACHE_DIR"] = inductor_cache

            rank = self.vllm_config.parallel_config.rank
            dp_rank = self.vllm_config.parallel_config.data_parallel_index
            cache_dir = os.path.join(cache_dir, f"rank_{rank}_{dp_rank}")
            aot_compilation_path = os.path.join(cache_dir, "model")
            if not envs.VLLM_DISABLE_COMPILE_CACHE:
                loaded_fn = _try_load_aot_compiled_fn(self, aot_compilation_path)
                if loaded_fn is not None:
                    self.aot_compiled_fn = loaded_fn
                    self.was_aot_compile_fn_loaded_from_disk = True
                    with (
                        monitor_profiling_run(),
                        maybe_use_cudagraph_partition_wrapper(self.vllm_config),
                    ):
                        output = self.aot_compiled_fn(self, *args, **kwargs)
                    return output

        if self.compiled:
            assert (
                not envs.VLLM_USE_AOT_COMPILE
                or self.vllm_config.compilation_config.backend == "eager"
            )
            return TorchCompileWithNoGuardsWrapper.__call__(self, *args, **kwargs)  # type: ignore[arg-type]

        # This is the path for the first compilation.
        # the first compilation needs to have dynamic shapes marked
        _mark_dynamic_inputs(
            self,
            ds_type,
            *args,
            **kwargs,
        )

        original_code_object = self.original_code_object()
        logger.debug("Start compiling function %s", original_code_object)

        # we do not want tp delete the original code object entries since
        # we depend on them now to look up cached compiled functions.
        # torch._dynamo.eval_frame.remove_from_cache(original_code_object)

        # collect all relevant files traced by Dynamo,
        # so that the compilation cache can trigger re-compilation
        # properly when any of these files change.

        # 1. the file containing the top-level forward function
        self.compilation_config.traced_files.add(original_code_object.co_filename)

        # 2. every time Dynamo sees a function call, it will inline
        # the function by calling InliningInstructionTranslator.inline_call_
        # we hijack this function to know all the functions called
        # during Dynamo tracing, and their corresponding files
        inline_call = InliningInstructionTranslator.inline_call_

        def patched_inline_call(self_: Any) -> Any:
            code = self_.f_code
            self.compilation_config.traced_files.add(code.co_filename)
            return inline_call(self_)

        # Disable the C++ compilation of symbolic shape guards. C++-fication
        # of symbolic shape guards can improve guard overhead. But, since
        # vllm skip guards anyways, setting this flag to False can improve
        # compile time.
        dynamo_config_patches = {}
        try:
            _ = torch._dynamo.config.enable_cpp_symbolic_shape_guards
            dynamo_config_patches["enable_cpp_symbolic_shape_guards"] = False
        except AttributeError:
            # Note: this config is not available in torch 2.6, we can skip
            # if the config doesn't exist
            logger.debug("enable_cpp_symbolic_shape_guards config not available")

        # Prepare backed_size_oblivious config patch if needed
        fx_config_patches = {}
        if ds_type == DynamicShapesType.BACKED_SIZE_OBLIVIOUS:
            fx_config_patches["backed_size_oblivious"] = True

        # Prepare inductor config patches
        # assume_32bit_indexing is only available in torch 2.10.0+
        inductor_config_patches = {}
        if is_torch_equal_or_newer("2.10.0"):
            inductor_config_patches["assume_32bit_indexing"] = (
                self.compilation_config.dynamic_shapes_config.assume_32_bit_indexing
            )

        with (
            patch.object(
                InliningInstructionTranslator, "inline_call_", patched_inline_call
            ),
            torch._dynamo.config.patch(**dynamo_config_patches),
            maybe_use_cudagraph_partition_wrapper(self.vllm_config),
            torch.fx.experimental._config.patch(**fx_config_patches),
            torch._inductor.config.patch(**inductor_config_patches),
        ):
            use_aot_compile = envs.VLLM_USE_AOT_COMPILE
            if self.vllm_config.compilation_config.backend == "eager":
                logger.warning("Detected eager backend, disabling AOT compile.")
                use_aot_compile = False
            if use_aot_compile:
                # store the path for saving after warmup
                self._aot_compilation_path = aot_compilation_path
                self._aot_cache_dir = cache_dir
                with monitor_torch_compile(
                    self.vllm_config, is_encoder=self._is_encoder
                ):
                    self.aot_compiled_fn = self.aot_compile(*args, **kwargs)
                    compilation_counter.num_aot_compiles += 1
                    # All compilation is done at this point, save the
                    # AOT artifact.
                    self.save_aot_compiled_function()

                with monitor_profiling_run():
                    output = self.aot_compiled_fn(self, *args, **kwargs)
            else:
                with monitor_torch_compile(
                    self.vllm_config,
                    "torch.compile and initial profiling/warmup "
                    "run together took %.2f s in total",
                    is_encoder=self._is_encoder,
                ):
                    output = TorchCompileWithNoGuardsWrapper.__call__(
                        self,  # type: ignore[arg-type]
                        *args,
                        **kwargs,
                    )

        self.compiled = True
        return output