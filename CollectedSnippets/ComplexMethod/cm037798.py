def __init__(
        self,
        num_experts: int,  # Global number of experts
        top_k: int,
        hidden_size: int,
        intermediate_size: int,
        params_dtype: torch.dtype | None = None,
        renormalize: bool = True,
        use_grouped_topk: bool = False,
        num_expert_group: int | None = None,
        topk_group: int | None = None,
        quant_config: QuantizationConfig | None = None,
        tp_size: int | None = None,
        ep_size: int | None = None,
        dp_size: int | None = None,
        pcp_size: int | None = None,
        prefix: str = "",
        custom_routing_function: Callable | None = None,
        scoring_func: str = "softmax",
        routed_scaling_factor: float = 1.0,
        e_score_correction_bias: torch.Tensor | None = None,
        apply_router_weight_on_input: bool = False,
        activation: str = "silu",
        is_act_and_mul: bool = True,
        enable_eplb: bool = False,
        num_redundant_experts: int = 0,
        has_bias: bool = False,
        is_sequence_parallel=False,
        expert_mapping: list[tuple[str, str, int, str]] | None = None,
        n_shared_experts: int | None = None,
        router_logits_dtype: torch.dtype | None = None,
        gate: torch.nn.Module | None = None,
        shared_experts: torch.nn.Module | None = None,
        routed_input_transform: torch.nn.Module | None = None,
        routed_output_transform: torch.nn.Module | None = None,
        apply_routed_scale_to_output: bool = False,
        zero_expert_type: str | None = None,
    ):
        super().__init__()

        if params_dtype is None:
            params_dtype = torch.get_default_dtype()
        self.params_dtype = params_dtype

        vllm_config = get_current_vllm_config()
        self.vllm_config = vllm_config

        # FIXME (varun): We should have a better way of inferring the activation
        # datatype. This works for now as the tensor datatype entering the MoE
        # operation is typically unquantized (i.e. float16/bfloat16).
        if vllm_config.model_config is not None:
            moe_in_dtype = vllm_config.model_config.dtype
        else:
            # TODO (bnell): This is a hack to get test_mixtral_moe to work
            # since model_config is not set in the pytest test.
            moe_in_dtype = params_dtype

        tp_size_ = (
            tp_size if tp_size is not None else get_tensor_model_parallel_world_size()
        )
        dp_size_ = dp_size if dp_size is not None else get_dp_group().world_size
        pcp_size_ = pcp_size if pcp_size is not None else get_pcp_group().world_size

        self.is_sequence_parallel = is_sequence_parallel
        self.sp_size = tp_size_ if is_sequence_parallel else 1

        self.moe_parallel_config: FusedMoEParallelConfig = FusedMoEParallelConfig.make(
            tp_size_=tp_size_,
            pcp_size_=pcp_size_,
            dp_size_=dp_size_,
            sp_size_=self.sp_size,
            vllm_parallel_config=vllm_config.parallel_config,
        )

        assert self.moe_parallel_config.is_sequence_parallel == is_sequence_parallel

        self.global_num_experts = num_experts + num_redundant_experts
        self.logical_num_experts = num_experts

        # Expert mapping used in self.load_weights
        self.expert_mapping = expert_mapping

        # For smuggling this layer into the fused moe custom op
        compilation_config = vllm_config.compilation_config
        if prefix in compilation_config.static_forward_context:
            raise ValueError("Duplicate layer name: {}".format(prefix))
        compilation_config.static_forward_context[prefix] = self
        compilation_config.static_all_moe_layers.append(prefix)
        self.layer_name = prefix

        self.enable_eplb = enable_eplb
        # TODO(bnell): should this be owned by router?
        self.eplb_state = EplbLayerState()
        self.expert_placement_strategy: ExpertPlacementStrategy = (
            vllm_config.parallel_config.expert_placement_strategy
        )

        # ROCm aiter shared experts fusion
        # AITER only supports gated activations (silu/gelu), so disable it
        # for non-gated MoE (is_act_and_mul=False)
        self.rocm_aiter_fmoe_enabled = (
            rocm_aiter_ops.is_fused_moe_enabled() and is_act_and_mul
        )
        self.aiter_fmoe_shared_expert_enabled = (
            rocm_aiter_ops.is_fusion_moe_shared_experts_enabled() and is_act_and_mul
        )

        self.num_fused_shared_experts = (
            n_shared_experts
            if n_shared_experts is not None and self.aiter_fmoe_shared_expert_enabled
            else 0
        )
        if (
            not self.aiter_fmoe_shared_expert_enabled
            and self.num_fused_shared_experts != 0
        ):
            raise ValueError(
                "n_shared_experts is only supported on ROCm aiter when "
                "VLLM_ROCM_USE_AITER_FUSION_SHARED_EXPERTS is enabled"
            )

        # Determine expert maps
        if self.use_ep:
            if self.enable_eplb:
                assert self.global_num_experts % self.ep_size == 0, (
                    "EPLB currently only supports even distribution of "
                    "experts across ranks."
                )
            else:
                assert num_redundant_experts == 0, (
                    "Redundant experts are only supported with EPLB."
                )

            self.expert_placement_strategy = determine_expert_placement_strategy(
                expert_placement_strategy=self.expert_placement_strategy,
                moe_parallel_config=self.moe_parallel_config,
                num_expert_group=num_expert_group,
                num_redundant_experts=num_redundant_experts,
                enable_eplb=self.enable_eplb,
            )

            self._expert_map: torch.Tensor | None
            local_num_experts, expert_map, expert_mask = determine_expert_map(
                ep_size=self.ep_size,
                ep_rank=self.ep_rank,
                global_num_experts=self.global_num_experts,
                expert_placement_strategy=self.expert_placement_strategy,
                num_fused_shared_experts=self.num_fused_shared_experts,
                return_expert_mask=self.rocm_aiter_fmoe_enabled,
            )
            self.local_num_experts = local_num_experts
            self.register_buffer("_expert_map", expert_map)
            self.register_buffer("expert_mask", expert_mask)
            self._maybe_init_expert_routing_tables()
            logger.info_once(
                "[EP Rank %s/%s] Expert parallelism is enabled. Expert "
                "placement strategy: %s. Local/global"
                " number of experts: %s/%s. Experts local to global index map:"
                " %s.",
                self.ep_rank,
                self.ep_size,
                self.expert_placement_strategy,
                self.local_num_experts,
                self.global_num_experts,
                get_compressed_expert_map(self._expert_map),
            )
        else:
            self.local_num_experts, self._expert_map, self.expert_mask = (
                self.global_num_experts,
                None,
                None,
            )

        self.top_k = top_k

        self._init_aiter_shared_experts_topK_buffer(
            vllm_config=vllm_config, dp_size=dp_size_
        )
        if self.use_ep and self.rocm_aiter_fmoe_enabled:
            assert self.expert_mask is None or torch.all(
                (expert_mask == 0) | (expert_mask == 1)
            ), "Aiter Fused MoE kernel only supports expert_map with 0 and 1s."

        assert intermediate_size % self.tp_size == 0
        intermediate_size_per_partition = intermediate_size // self.tp_size
        self.renormalize = renormalize

        # TODO(bnell): these attributes are only used by monolithic kernels.
        # Put them in a MoERouterConfig dataclass?
        self.use_grouped_topk = use_grouped_topk
        if self.use_grouped_topk:
            assert num_expert_group is not None and topk_group is not None
        self.num_expert_group = num_expert_group
        self.topk_group = topk_group
        self.custom_routing_function = custom_routing_function
        self.scoring_func = scoring_func
        # When apply_routed_scale_to_output is True, we set the scaling factor
        # to 1.0 so it ends up being a nop. Applying the scale will be handled
        # by the runner in this case.
        # The member variable must be set in the same way as the router since
        # some quantization methods can access it.
        self.routed_scaling_factor = (
            routed_scaling_factor if not apply_routed_scale_to_output else 1.0
        )
        self.e_score_correction_bias = e_score_correction_bias
        # TODO(bnell): end attributes

        self.apply_router_weight_on_input = apply_router_weight_on_input
        self.activation = MoEActivation.from_str(activation)

        # TODO(bnell): we should not have to create a router if the kernel is
        # monolithic.
        self.router = create_fused_moe_router(
            top_k=top_k,
            global_num_experts=self.global_num_experts,
            eplb_state=self.eplb_state,
            renormalize=renormalize,
            use_grouped_topk=use_grouped_topk,
            num_expert_group=num_expert_group,
            topk_group=topk_group,
            custom_routing_function=custom_routing_function,
            scoring_func=scoring_func,
            routed_scaling_factor=self.routed_scaling_factor,
            e_score_correction_bias=e_score_correction_bias,
            num_fused_shared_experts=self.num_fused_shared_experts,
            enable_eplb=enable_eplb,
            # TODO(bnell): once we can construct the MK at init time, we
            # can make this a value.
            indices_type_getter=lambda: self.quant_method.topk_indices_dtype,
            zero_expert_type=zero_expert_type,
            num_logical_experts=self.logical_num_experts,
        )
        self.routing_method_type: RoutingMethodType = self.router.routing_method_type

        self.moe_config: FusedMoEConfig = FusedMoEConfig(
            num_experts=self.global_num_experts,
            experts_per_token=top_k,
            hidden_dim=hidden_size,
            hidden_dim_unpadded=hidden_size,
            intermediate_size_per_partition=intermediate_size_per_partition,
            intermediate_size_per_partition_unpadded=intermediate_size_per_partition,
            num_local_experts=self.local_num_experts,
            num_logical_experts=self.logical_num_experts,
            moe_parallel_config=self.moe_parallel_config,
            in_dtype=moe_in_dtype,
            moe_backend=vllm_config.kernel_config.moe_backend,
            router_logits_dtype=router_logits_dtype,
            max_num_tokens=vllm_config.scheduler_config.max_num_batched_tokens,
            has_bias=has_bias,
            is_act_and_mul=is_act_and_mul,
            is_lora_enabled=vllm_config.lora_config is not None,
            activation=self.activation,
            device=vllm_config.device_config.device,
            routing_method=self.routing_method_type,
            # TODO: in_dtype == out_dtype?
            disable_inplace=disable_inplace() or shared_experts is not None,
        )
        if self.moe_config.use_mori_kernels:
            assert self.rocm_aiter_fmoe_enabled, (
                "Mori needs to be used with aiter fused_moe for now."
            )
            assert not self.aiter_fmoe_shared_expert_enabled, (
                "Mori does not support fusion shared expert now. "
                "Turn it off by setting VLLM_ROCM_USE_AITER_FUSION_SHARED_EXPERTS=0"
            )

        self.quant_config = quant_config

        def _get_quant_method() -> FusedMoEMethodBase:
            """
            Helper method to ensure self.quant_method is never None and
            of the proper type.
            """
            quant_method = None
            if self.quant_config is not None:
                quant_method = self.quant_config.get_quant_method(self, prefix)
            if quant_method is None:
                quant_method = UnquantizedFusedMoEMethod(self.moe_config)
            assert isinstance(quant_method, FusedMoEMethodBase)
            return quant_method

        # Note: get_quant_method will look at the layer's local_num_experts
        # for heuristic purposes, so it must be initialized first.
        self.quant_method: FusedMoEMethodBase = _get_quant_method()

        if not self.moe_config.is_act_and_mul and not current_platform.is_cuda_alike():
            raise NotImplementedError(
                "is_act_and_mul=False is supported only for CUDA and ROCm for now"
            )

        if self.enable_eplb and not self.quant_method.supports_eplb:
            # TODO: Add support for additional quantization methods.
            # The implementation for other quantization methods does not
            # contain essential differences, but the current quant API
            # design causes duplicated work when extending to new
            # quantization methods, so I'm leaving it for now.
            # If you plan to add support for more quantization methods,
            # please refer to the implementation in `Fp8MoEMethod`.
            raise NotImplementedError(
                f"EPLB is not supported {self.quant_method.__class__.__name__}."
            )

        # Round up hidden size and update moe_config.
        hidden_size, intermediate_size_per_partition = (
            self.quant_method.maybe_roundup_sizes(
                hidden_size,
                intermediate_size_per_partition,
                moe_in_dtype,
                self.moe_parallel_config,
            )
        )
        self.moe_config.hidden_dim = hidden_size
        self.moe_config.intermediate_size_per_partition = (
            intermediate_size_per_partition
        )

        moe_quant_params = {
            "num_experts": self.local_num_experts,
            "hidden_size": hidden_size,
            "intermediate_size_per_partition": intermediate_size_per_partition,
            "params_dtype": params_dtype,
            "weight_loader": self.weight_loader,
            "global_num_experts": self.global_num_experts,
        }
        # need full intermediate size pre-sharding for WNA16 act order
        if self.quant_method.__class__.__name__ in (
            "GPTQMarlinMoEMethod",
            "CompressedTensorsWNA16MarlinMoEMethod",
            "CompressedTensorsWNA16MoEMethod",
        ):
            moe_quant_params["intermediate_size_full"] = intermediate_size

        self.quant_method.create_weights(layer=self, **moe_quant_params)

        # TODO(bnell): this is un-needed and removed in a follow up PR.
        self.base_quant_method = self.quant_method

        # Storing the runner in the FusedMoE is an intermediate state, eventually
        # the runner will own the FusedMoE layer and provide the execution interface
        # for MoE ops.
        self.runner: MoERunnerInterface = MoERunner(
            layer_name=self.layer_name,
            moe_config=self.moe_config,
            router=self.router,
            gate=gate,
            shared_experts=shared_experts,
            quant_method=self.quant_method,
            enable_dbo=self.vllm_config.parallel_config.enable_dbo,
            routed_input_transform=routed_input_transform,
            routed_output_transform=routed_output_transform,
            # When apply_routed_scale_to_output is True, we allow
            # the scaling factor to be passed to the runner, otherwise
            # we pass 1.0 so it ends up being a nop.
            routed_scaling_factor=routed_scaling_factor
            if apply_routed_scale_to_output
            else 1.0,
        )