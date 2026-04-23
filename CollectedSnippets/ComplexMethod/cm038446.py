def switch_and_prepare(self) -> None:
        old_dp_size = get_dp_group().world_size
        old_ep_size = get_ep_group().world_size

        self._release_cuda_graphs()
        _replace_active_groups(**pop_standby_groups())

        parallel_config = self.worker.vllm_config.parallel_config
        reconfig_request = self.reconfig_request
        assert reconfig_request is not None
        new_dp_size = reconfig_request.new_data_parallel_size
        new_ep_size = get_ep_group().world_size

        parallel_config.data_parallel_size = new_dp_size
        if (
            reconfig_request.new_data_parallel_rank
            != ReconfigureRankType.KEEP_CURRENT_RANK
        ):
            parallel_config.data_parallel_rank = reconfig_request.new_data_parallel_rank
        if (
            reconfig_request.new_data_parallel_rank_local
            != ReconfigureRankType.KEEP_CURRENT_RANK
        ):
            parallel_config.data_parallel_rank_local = (
                reconfig_request.new_data_parallel_rank_local
            )
        parallel_config.data_parallel_master_ip = (
            reconfig_request.new_data_parallel_master_ip
        )
        parallel_config.data_parallel_master_port = (
            reconfig_request.new_data_parallel_master_port
        )

        # Reconfigure MoE modules with new EP size
        moe_modules = [
            module
            for module in self.worker.model_runner.model.modules()
            if is_moe_layer(module)
        ]
        num_local_experts = moe_modules[0].moe_config.num_local_experts
        assert all(
            module.moe_config.num_local_experts == num_local_experts
            for module in moe_modules
        ), "All MoE modules must have the same number of experts"
        for module in moe_modules:
            module.moe_config.num_experts = num_local_experts * new_ep_size
            module.global_num_experts = module.moe_config.num_experts
            tp_size = get_tp_group().world_size
            is_sequence_parallel = parallel_config.use_sequence_parallel_moe
            sp_size = tp_size if is_sequence_parallel else 1
            module.moe_parallel_config = FusedMoEParallelConfig.make(
                tp_size_=tp_size,
                pcp_size_=get_pcp_group().world_size,
                dp_size_=get_dp_group().world_size,
                sp_size_=sp_size,
                vllm_parallel_config=parallel_config,
            )
            module.moe_config.moe_parallel_config = module.moe_parallel_config

        # Update EPLB state
        eplb_state = self.worker.model_runner.eplb_state
        assert eplb_state is not None
        model_config = self.worker.model_runner.model_config
        eplb_model_state = eplb_state.model_states[model_config.compute_hash()]

        num_physical_experts = num_local_experts * new_ep_size
        num_logical_experts = eplb_model_state.logical_replica_count.shape[1]
        parallel_config.eplb_config.num_redundant_experts = (
            num_physical_experts - num_logical_experts
        )
        old_physical_to_logical = eplb_model_state.physical_to_logical_map
        num_moe_layers = old_physical_to_logical.shape[0]
        num_local_experts = eplb_model_state.expert_load_pass.shape[1] // old_ep_size
        if new_dp_size > old_dp_size:
            expanded_physical_to_logical = torch.full(
                (num_moe_layers, num_local_experts * new_ep_size),
                -1,
                dtype=old_physical_to_logical.dtype,
                device=old_physical_to_logical.device,
            )
            expanded_physical_to_logical[:, : num_local_experts * old_ep_size] = (
                old_physical_to_logical
            )
            eplb_model_state.physical_to_logical_map = expanded_physical_to_logical

        old_num_physical_experts = eplb_model_state.expert_load_pass.shape[1]
        pad_size = num_physical_experts - old_num_physical_experts
        if new_dp_size > old_dp_size:
            assert pad_size > 0
            expanded_expert_load_pass = F.pad(
                eplb_model_state.expert_load_pass, (0, pad_size), value=0
            )
            expanded_expert_load_window = F.pad(
                eplb_model_state.expert_load_window, (0, pad_size), value=0
            )
            eplb_model_state.expert_load_pass = expanded_expert_load_pass
            eplb_model_state.expert_load_window = expanded_expert_load_window
            eplb_state.num_valid_physical_experts = old_num_physical_experts
        else:
            assert pad_size < 0
            eplb_model_state.expert_load_pass = eplb_model_state.expert_load_pass[
                :, :num_physical_experts
            ]
            eplb_model_state.expert_load_window = eplb_model_state.expert_load_window[
                :, :, :num_physical_experts
            ]
            eplb_state.num_valid_physical_experts = num_physical_experts

        model = self.worker.model_runner.get_model()
        model.expert_weights = []
        with set_current_vllm_config(self.worker.vllm_config):
            model.set_eplb_state(
                eplb_model_state.expert_load_pass,
                eplb_model_state.logical_to_physical_map,
                eplb_model_state.logical_replica_count,
            )
            eplb_state._init_should_record_tensor(model)
            model.update_physical_experts_metadata(
                num_physical_experts=num_physical_experts,
                num_local_physical_experts=num_local_experts,
            )
            # Force re-creation of the modular kernel (and all2all manager)
            # for the new EP size by resetting quant_method to base
            for module in moe_modules:
                if hasattr(module.quant_method, "old_quant_method"):
                    module._replace_quant_method(module.quant_method.old_quant_method)
            prepare_communication_buffer_for_model(self.worker.model_runner.model)

        eplb_model_state.communicator = create_eplb_communicator(
            group_coordinator=get_eplb_group(),
            backend=parallel_config.eplb_config.communicator,
            expert_weights=model.expert_weights[0],
        )

        if (
            self.worker.vllm_config.compilation_config.mode
            == CompilationMode.STOCK_TORCH_COMPILE
        ):
            # NOTE(yongji): when using stock torch.compile,
            # torch.compile is triggered during GPUModelRunner's load_model()
            # TODO(yongji):check do we need to re-trigger torch.compile here?
            # any changes to the tensor shapes in execution should already
            # be handled internally by torch.compile.
            backend = self.worker.vllm_config.compilation_config.init_backend(
                self.worker.vllm_config
            )
            compilation_counter.stock_torch_compile_count += 1
            self.worker.model_runner.model.compile(fullgraph=True, backend=backend)

        multi_block_table = self.worker.model_runner.input_batch.block_table
        saved_block_tables: list[tuple[torch.Tensor, torch.Tensor]] = []
        for bt in multi_block_table.block_tables:
            saved_block_tables.append(
                (bt.block_table.gpu.clone(), bt.block_table.cpu.clone())
            )
        multi_block_table.clear()

        unlock_workspace()
        self.worker.compile_or_warm_up_model()
        lock_workspace()

        for bt, (saved_gpu, saved_cpu) in zip(
            multi_block_table.block_tables, saved_block_tables
        ):
            bt.block_table.gpu.copy_(saved_gpu)
            bt.block_table.cpu.copy_(saved_cpu)
        if new_dp_size < old_dp_size:
            self._set_eplb_suppressed(False)