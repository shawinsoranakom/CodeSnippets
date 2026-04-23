def rearrange(
        self,
        is_profile: bool = False,
        rank_mapping: dict[int, int] | None = None,
    ) -> torch.Tensor | None:
        """
        Rearrange the experts according to the current load.

        Args:
            is_profile (bool): If `True`, perform a dummy rearrangement.
                This is used in `profile_run` to reserve enough memory,
                no memory movement will be performed. Default is False.
            rank_mapping (dict[int, int] | None): The rank mapping
                when scaling is done in EEP.
        """

        ep_group = get_ep_group().device_group
        ep_rank = ep_group.rank()

        start_event = None
        end_event = None
        is_main_rank = ep_rank == 0
        if is_main_rank:
            if not self.is_async or is_profile:
                start_event = torch.cuda.Event(enable_timing=True)
                end_event = torch.cuda.Event(enable_timing=True)
                start_event.record()
            logger.info(
                "Rearranging experts %s %s...",
                "(async mode)" if self.is_async else "sync mode",
                "(profile)" if is_profile else "",
            )

        # Map the physical expert load to global logical experts
        global_expert_load_windows = []
        for eplb_model_state in self.model_states.values():
            expert_load_window = eplb_model_state.expert_load_window[
                :, :, : self.num_valid_physical_experts
            ]
            logical_expert_load_window = torch.zeros(
                self.expert_load_window_size,
                eplb_model_state.model.num_moe_layers,
                eplb_model_state.model.num_logical_experts,
                dtype=eplb_model_state.expert_load_window.dtype,
                device=eplb_model_state.expert_load_window.device,
            )
            logical_expert_load_window.scatter_add_(
                dim=-1,
                index=eplb_model_state.physical_to_logical_map[
                    :, : self.num_valid_physical_experts
                ]
                .unsqueeze(0)
                .expand_as(expert_load_window)
                .long(),
                src=expert_load_window,
            )

            global_expert_load_window = logical_expert_load_window.sum(dim=0)
            global_expert_load_windows.append(global_expert_load_window)
        # Perform all-reduce to get the expert load across all ranks for each model
        global_expert_load_windows = self._allreduce_list(global_expert_load_windows)

        # TODO(bowen): Treat differently for prefill and decode nodes
        eplb_model_state = next(iter(self.model_states.values()))
        model = eplb_model_state.model
        num_replicas = model.num_physical_experts
        num_groups = model.num_expert_groups

        if rank_mapping is not None and len(rank_mapping) == ep_group.size():
            # NOTE(yongji): scale down, we need to rebalance the experts on
            # remaining GPUs, transfer the experts while we haven't shutdown
            # the GPUs to be released.
            coordinator = get_ep_group()
            assert isinstance(coordinator, StatelessGroupCoordinator)
            tcp_store_group = coordinator.tcp_store_group
            num_nodes = _node_count_with_rank_mapping(tcp_store_group, rank_mapping)
            num_gpus = sum(new_rank != -1 for new_rank in rank_mapping.values())
            num_replicas = (
                num_replicas // ep_group.size() * num_gpus
            )  # handle num replicas change
        else:
            num_nodes = get_node_count()
            num_gpus = ep_group.size()

        if num_gpus % num_nodes != 0:
            num_nodes = 1
            logger.warning_once(
                f"num_gpus % num_nodes != 0, "
                "not using hierarchical rearrangement algorithm.\n"
                f"{num_gpus=}, {num_nodes=}"
            )

        # Get new expert mappings
        for eplb_model_state, global_expert_load_window in zip(
            self.model_states.values(), global_expert_load_windows
        ):
            if not self.is_async or is_profile:
                # Get new expert mappings for the model
                new_physical_to_logical_map = self.policy.rebalance_experts(
                    global_expert_load_window.cpu(),
                    num_replicas,
                    num_groups,
                    num_nodes,
                    num_gpus,
                    eplb_model_state.physical_to_logical_map.cpu(),
                )

                # Update expert weights
                rearrange_expert_weights_inplace(
                    eplb_model_state.physical_to_logical_map,
                    new_physical_to_logical_map,
                    eplb_model_state.model.expert_weights,
                    ep_group,
                    eplb_model_state.communicator,
                    is_profile,
                    rank_mapping,
                )

                if not is_profile:
                    _commit_eplb_maps(
                        eplb_model_state,
                        new_physical_to_logical_map=new_physical_to_logical_map,
                    )

                if is_main_rank:
                    assert start_event is not None
                    assert end_event is not None
                    end_event.record()
                    end_event.synchronize()
                    gpu_elapsed = start_event.elapsed_time(end_event) / 1000.0
                    logger.info(
                        "Rearranged experts %s in %.2f s.",
                        " (profile) " if is_profile else " ",
                        gpu_elapsed,
                    )
            else:
                eplb_model_state.eplb_stats = EplbStats(
                    # We copy the tensor to snapshot the global_expert_load_window
                    # on the main thread so that async worker can access it safely
                    # while the main thread is running.
                    global_expert_load_window=global_expert_load_window.clone(),
                    num_replicas=num_replicas,
                    num_groups=num_groups,
                    num_nodes=num_nodes,
                    num_gpus=num_gpus,
                )
                eplb_model_state.rebalanced = True
        # Signal async thread to start transferring layers
        if self.is_async and (not is_profile):
            self.rearrange_event.record()
        return None