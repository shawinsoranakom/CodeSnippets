def __init__(
        self,
        gm: torch.fx.GraphModule,
        example_inputs: Sequence[InputType],
        fx_kwargs: _CompileFxKwargs,
        inputs_to_check: Sequence[int],
    ) -> None:
        self.gm = gm
        # Replace opaque references with hashable ordinals. What's important
        # is that if the same reference appears twice then it's the same hash
        # value for each.
        processed_inputs: list[InputType | HashableOpaqueValue] = []
        seen_opaques: dict[int, HashableOpaqueValue] = {}
        for inp in example_inputs:
            if is_opaque_reference_type(type(inp)):
                if id(inp) not in seen_opaques:
                    seen_opaques[id(inp)] = HashableOpaqueValue(len(seen_opaques))
                processed_inputs.append(seen_opaques[id(inp)])
            else:
                processed_inputs.append(inp)
        self.example_inputs = processed_inputs
        self.cache_key_tag = cconfig.cache_key_tag

        # Order kwargs so hashing is stable to changes in kwarg order. Although
        # it's technically a _CompileFxKwargs we don't actually need it typed as
        # such since we're just using it to generate a hash.
        self.fx_kwargs: dict[str, object] = {}
        for k, v in sorted(fx_kwargs.items()):
            if k not in self.EXCLUDED_KWARGS:
                if type(v) in (set, OrderedSet):  # noqa: set_linter
                    # Special case to handle set params. Python sets can't be
                    # ordered, so sort the elements and store them in a proxy.
                    self.fx_kwargs[k] = OrderedSetHolder(sorted(v))  # type: ignore[call-overload]
                else:
                    self.fx_kwargs[k] = v

        from torch._higher_order_ops.triton_kernel_wrap import (
            kernel_side_table,
            triton_kernel_wrapper_functional,
            triton_kernel_wrapper_mutation,
        )
        from torch._inductor.codegen.wrapper import (
            user_defined_triton_kernel_transitive_closure_source_code,
        )

        # Node meta will not be part of gm's reduce function, so lets remember
        # the kernel source code separately
        self.user_defined_triton_source: list[Any] = []
        if gm is not None:
            for module in gm.modules():
                if not isinstance(module, torch.fx.GraphModule):
                    continue
                for node in itertools.chain(
                    module.graph.find_nodes(
                        op="call_function", target=triton_kernel_wrapper_functional
                    ),
                    module.graph.find_nodes(
                        op="call_function", target=triton_kernel_wrapper_mutation
                    ),
                ):
                    from triton.runtime.autotuner import Autotuner

                    kernel = kernel_side_table.get_kernel(node.kwargs["kernel_idx"])
                    configs = None
                    if isinstance(kernel, Autotuner):
                        if kernel.configs:
                            configs = str(
                                sorted(
                                    sorted(str(kv) for kv in c.all_kwargs().items())
                                    for c in kernel.configs
                                )
                            )
                        kernel = kernel.fn

                    kernel_source = (
                        user_defined_triton_kernel_transitive_closure_source_code(
                            kernel
                        )
                    )
                    constant_args = kernel_side_table.get_constant_args(
                        node.kwargs["constant_args_idx"]
                    )
                    self.user_defined_triton_source.append(
                        (kernel_source, constant_args, configs)
                    )

        # Alignment checks
        self.inputs_to_check = inputs_to_check

        no_tensor_inputs = not any(isinstance(x, torch.Tensor) for x in example_inputs)
        # This device index is usually already encoded by the device of the inputs
        # but fx graphs don't necessarily have tensor inputs. If there aren't any,
        # we need to guard on the device index in case we allocate cuda tensors
        if no_tensor_inputs and torch.accelerator.is_available():
            self.default_cuda_device_index = torch.accelerator.current_device_index()

        # 'Deterministic algorithms' can affect codegen via lowering to cuda kernels.
        self.deterministic_algorithms_settings = (
            torch.are_deterministic_algorithms_enabled(),
            torch.is_deterministic_algorithms_warn_only_enabled(),
            torch.utils.deterministic.fill_uninitialized_memory,  # type: ignore[attr-defined]
        )

        # Provenance tracking level affects whether provenance data is stored
        # in the CompiledFxGraph, so it must be part of the cache key.
        # Note: the "trace" prefix is excluded from _cache_config_ignore_prefix,
        # so we add this explicitly.
        self.provenance_tracking_level = config.trace.provenance_tracking_level

        # Global settings affecting matmul codegen.
        self.cuda_matmul_settings = (
            torch.backends.cuda.matmul.fp32_precision,
            torch.backends.cuda.matmul.allow_fp16_reduced_precision_reduction,
            torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction,
        )

        # Include cudagraph annotation in cache key only when it changes
        # behavior. When both fwd and bwd are overridden to the same value,
        # normalize to a simple boolean (equivalent to flipping the config).
        # When fwd and bwd differ, include the full annotation.
        if gm is not None:
            annotation = gm.meta.get("cudagraph_annotation")
            if annotation is not None:
                default = config.triton.cudagraphs
                if annotation.fwd == annotation.bwd and annotation.fwd is not None:
                    if annotation.fwd != default:
                        self.cudagraph_override = annotation.fwd
                elif (annotation.fwd is not None and annotation.fwd != default) or (
                    annotation.bwd is not None and annotation.bwd != default
                ):
                    self.cudagraph_annotation = annotation

        # Also hash on various system info (including the triton compiler version).
        self.torch_version = torch_key()
        self.system_info = CacheBase.get_system()
        self.inductor_config = config.save_config_portable(ignore_private_configs=False)
        # Custom passes should provide an ID to hash when they run late (after cache lookup).
        if resolve_pre_grad_pass_timing() != "early":
            self.pre_grad_custom_pass = self._get_custom_pass_detail(
                config.pre_grad_custom_pass
            )
        self.post_grad_custom_pre_pass = self._get_custom_pass_detail(
            config.post_grad_custom_pre_pass
        )
        # TODO: change to more holistic config rather than bundled_autograd_cache
        self.precompile_enabled = torch._functorch.config.bundled_autograd_cache
        self.post_grad_custom_post_pass = self._get_custom_pass_detail(
            config.post_grad_custom_post_pass
        )
        self.joint_custom_pre_pass = self._get_custom_pass_detail(
            config.joint_custom_pre_pass
        )
        self.joint_custom_post_pass = self._get_custom_pass_detail(
            config.joint_custom_post_pass
        )
        self._pre_fusion_custom_pass = self._get_custom_pass_detail_unsafe(
            config._pre_fusion_custom_pass
        )
        self._fuse_ddp_communication_passes = self._get_custom_pass_detail_unsafe(
            config._fuse_ddp_communication_passes
        )

        # Register indcutor backends and custom passes and get their UUIDs.
        init_backend_registration()
        self.custom_backend_passes = tuple(
            map(self._get_custom_pass_detail, custom_backend_passes.values())
        )

        # Save custom inductor codegen configs
        self.custom_backend_codegen_configs = {
            device: custom_config.save_config_portable(ignore_private_configs=False)
            for device, custom_config in custom_backend_codegen_configs.items()
            if custom_config is not None
        }

        # Register the custom partitioner function
        self._custom_partitioner_fn = self._get_custom_partitioner_fn_detail(
            config.custom_partitioner_fn
        )

        # Include hint overrides in the cache key because _reduce_symint
        # only hashes symbol names, not hint values.
        self.var_to_hint_override: dict[str, int] = {}
        shape_env = FxGraphCache._get_shape_env()
        if shape_env is not None and shape_env.var_to_hint_override:
            self.var_to_hint_override = {
                str(sym): val
                for sym, val in sorted(
                    shape_env.var_to_hint_override.items(), key=lambda x: str(x[0])
                )
            }