def resolve_compile_configs(
        self, fallback_compile_config: CompileConfig | None, is_flash_attn: bool, decode_fast_path_available: bool
    ) -> None:
        """Resolve if the compile configs for varlen and decode paths, modifying these attributes in place if needed.
        Default config use full compile over regional compile, because the throughput is significantly higher (~15%)"""
        logger_ = logging.get_logger("ContinuousBatchingLogger")

        # For each config, priority is: explicit config, default config, fallback config, None
        if self.varlen_compile_config is None:
            if self.use_default_compile_configs:
                # We don't use compile with flash varlen, because max_seqlen_k is volatile and introduces recompilations
                if is_flash_attn:
                    varlen_config = None
                else:
                    varlen_config = CompileConfig(mode="max-autotune-no-cudagraphs", fullgraph=True, dynamic=True)
            elif fallback_compile_config is not None:
                varlen_config = fallback_compile_config
            else:
                varlen_config = None
        else:
            varlen_config = self.varlen_compile_config

        if self.decode_compile_config is None:
            if self.use_default_compile_configs:
                # Paged attention is wrapped in @torch.compiler.disable so we can't use fullgraph
                decode_config = CompileConfig(mode="max-autotune-no-cudagraphs", fullgraph=False, dynamic=False)
            elif fallback_compile_config is not None:
                decode_config = fallback_compile_config
            else:
                decode_config = None
        else:
            decode_config = self.decode_compile_config

        # For decode, we throw a warning if the fast decode path is not available and a compile config was found
        if not decode_fast_path_available and self.decode_compile_config is not None:
            decode_config = None
            logger_.warning("A decode_compile_config was set but fast decode path is not available. Ignoring it.")

        # Log what will be compiled
        if varlen_config is not None:
            logger_.info(f"Varlen path will be compiled with {varlen_config.to_dict()}")
        if decode_config is not None:
            logger_.info(f"Decode path will be compiled with {decode_config.to_dict()}")
        # Modify in place
        self.varlen_compile_config = varlen_config
        self.decode_compile_config = decode_config