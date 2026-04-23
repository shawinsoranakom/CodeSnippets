def post_compile(
        self,
        example_inputs: Sequence[InputType],
        constants: CompiledFxGraphConstants,
        graph_kwargs: _CompileFxKwargs,
    ) -> None:
        """
        Run a set of post processing steps after loading from the cache. These involve:
         - Setting the tracing context output strides
         - Running cudagraphs if enabled
         - Realigning inputs

        This runs whether or not we have a cache hit, and always runs directly after we get a CompiledFxGraph.
        The results of this function are *not* saved in the cache itself.
        """
        if config.graph_partition and _unstable_customized_partition_wrapper.wrapper:
            # Mechanically apply user-specified cudagraph wrappers without modification
            assert self.recursively_apply_fns is not None
            assert self.compiled_fn_runner is not None
            num_partitions = len(self.compiled_fn_runner.partitions)
            wrapper_metadatas = [
                CUDAGraphWrapperMetadata(num_partitions, i)
                for i in range(num_partitions)
            ]
            customized_wrapper = _unstable_customized_partition_wrapper.wrapper
            customized_wrappers_with_metadata = [
                lambda f, m=metadata: customized_wrapper(f, m)
                for metadata in wrapper_metadatas
            ]
            self.recursively_apply_fns(customized_wrappers_with_metadata)
            return

        set_tracing_context_output_strides(example_inputs, self)
        assert graph_kwargs["cudagraphs"] is not None
        assert graph_kwargs["is_backward"] is not None
        is_backward = graph_kwargs["is_backward"]
        cudagraphs: BoxedBool = graph_kwargs["cudagraphs"]

        # When a CUDAGraphPolicy is set and it says not to wrap this
        # inner CompiledFxGraph (e.g. because wrapping happens at the
        # outer level via policy.wrap_output), disable cudagraphs for
        # this graph so the rest of post_compile (input realignment,
        # _wrap_compiled_regions) still runs normally.
        policy = config.cudagraph_policy
        if policy is not None and not policy.should_wrap(self):
            counters["inductor"]["cudagraph_skips"] += 1
            BoxedBool.disable(cudagraphs)

        if cudagraphs:
            # It's possible that cudagraphs is enabled, but was disabled
            # during a previous compilation we're loading from the cache.
            # If so, we need to disable it on this new process too.
            if self.disabled_cudagraphs_reason:
                if "cuda" in self.device_types:
                    log_cudagraph_skip_and_bump_counter(
                        f"skipping cudagraphs due to {self.disabled_cudagraphs_reason}"
                    )
                else:
                    counters["inductor"]["cudagraph_skips"] += 1
                BoxedBool.disable(cudagraphs)
            else:
                if is_backward:
                    assert "boxed_forward_device_index" in graph_kwargs
                    boxed_forward_device_index = graph_kwargs[
                        "boxed_forward_device_index"
                    ]
                else:
                    # On the forward we don't know whether or not
                    # boxed_forward_device_index is set yet
                    boxed_forward_device_index = graph_kwargs.get(
                        "boxed_forward_device_index", None
                    )

                if config.graph_partition and policy is None:
                    # With graph_partition=True, we skip some cudagraph checks
                    # if it's supported with partition, so we use
                    # cudagraph_partition_post_compile.  When a CUDAGraphPolicy
                    # is active, we use cudagraph_post_compile instead so the
                    # policy controls wrapping via policy.cudagraphify().
                    cudagraph_partition_post_compile(
                        example_inputs,
                        self,
                        cudagraphs,
                        constants.unwrap(self),
                        boxed_forward_device_index,
                    )
                else:
                    cudagraph_post_compile(
                        example_inputs,
                        self,
                        cudagraphs,
                        constants.unwrap(self),
                        boxed_forward_device_index,
                    )
        inputs_to_check = self.inputs_to_check
        # cudagraphs could have been disabled from the earlier conditions
        # so we still need to realign inputs if that happens
        maybe_realign_inputs(
            cudagraphs,
            self,
            inputs_to_check,
            self.mutated_input_idxs,
        )

        # Apply inductor_compiled_code HOP wrapper if configured
        # This is done in post_compile to ensure it works with cached artifacts
        if self._wrap_compiled_regions and self.current_callable is not None:
            from torch._higher_order_ops.wrap import InductorCompiledCallable

            original_callable = self.current_callable

            inductor_callable = InductorCompiledCallable(
                original_callable,
                self._original_gm,
                compile_region_name=self.compile_region_name,
            )

            def wrapped_callable(inputs):
                if is_in_torch_dispatch_mode():
                    kwargs = (
                        {"name": self.compile_region_name}
                        if self.compile_region_name is not None
                        else {}
                    )
                    return inductor_compiled_code(inductor_callable, inputs, **kwargs)
                else:
                    return original_callable(inputs)

            self.current_callable = wrapped_callable