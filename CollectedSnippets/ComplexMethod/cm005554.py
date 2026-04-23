def decide_use_cuda_graphs(self, compile_config: CompileConfig | None, is_attn_mask_needed: bool) -> None:
        """Decides whether or not to use cuda graphs for continuous batching. If the user specified this in the config
        or if they specified a parameter related to cuda graphs, they are turned on. Otherwise, we use a heuristic
        based on the attention implementation: we turn on cuda graphs if and only if no attention mask is needed.

        This function modifies the `use_cuda_graph` attribute of the config in place, to a tuple of booleans.
        """
        # If cuda is not available, we cannot use cuda graphs
        import torch

        if not torch.cuda.is_available():
            intended_use_cuda_graph = any(self.get_cuda_graph_booleans())
            if intended_use_cuda_graph:  # throw a warning only if the user intended to use cuda graphs
                logger.warning(f"{self.use_cuda_graph = } but {torch.cuda.is_available() = }: turning off cuda graphs")
            self.use_cuda_graph = (False, False)

        # Else if use_cuda_graph is specified, we follow the user's choice and make sure it is a tuple of booleans
        elif self.use_cuda_graph is not None:
            if isinstance(self.use_cuda_graph, bool):
                self.use_cuda_graph = (self.use_cuda_graph, self.use_cuda_graph)

        # Else if the user specified a parameter related to cuda graphs, we activate cuda graphs
        elif self.q_padding_interval_size or self.kv_padding_interval_size or self.max_cached_graphs:
            self.use_cuda_graph = (True, True)

        # Else if a compile config was found, turn off cuda graphs if the compile config already uses them
        elif compile_config is not None:
            options = torch._inductor.list_mode_options().get(compile_config.mode, compile_config.options)
            compile_uses_cudagraphs = options.get("triton.cudagraphs", False)
            if compile_uses_cudagraphs:
                logger.warning(
                    f"Compile config {compile_config.mode = } uses cudagraphs, which usually does not work well with "
                    "continuous batching. We recommend using mode 'default' or 'max-autotune-no-cudagraphs' instead."
                )
            use_cuda_graph = not compile_uses_cudagraphs  # TODO: should this also match the dynamic shapes?
            self.use_cuda_graph = (use_cuda_graph, use_cuda_graph)

        # Otherwise we have a default heuristic based on the attention implementation:
        # attention implementations where an attention mask is needed suffer a lot more from the padding associated
        # with cuda graphs, so default is to turn cuda graphs off for those implementations
        else:
            use_cuda_graph = not is_attn_mask_needed
            self.use_cuda_graph = (use_cuda_graph, use_cuda_graph)
            logger.warning(
                f"No behavior specified for use_cuda_graph, defaulting to {self.use_cuda_graph = } because "
                f"{is_attn_mask_needed = }. If you want to save memory, turn off cuda graphs, but they tend to improve "
                "performances by a lot."
            )