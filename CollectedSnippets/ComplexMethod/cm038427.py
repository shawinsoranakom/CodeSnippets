def step(
        self,
        is_dummy: bool = False,
        is_profile: bool = False,
        log_stats: bool = False,
    ) -> None:
        """
        Step the EPLB state.

        Args:
            is_dummy (bool): If `True`, this is a dummy step and the load
                metrics recorded in this forward pass will not count.
                Defaults to `False`.
            is_profile (bool): If `True`, perform a dummy rearrangement
                with maximum communication cost. This is used in
                `profile_run` to reserve enough memory
                for the communication buffer.
            log_stats (bool): If `True`, log the expert load metrics.

        # Stats
            The metrics are all summed up across layers.
            - `avg_tokens`: The average load across ranks.
            - `max_tokens`: The maximum load across ranks.
            - `balancedness`: The ratio of average load to maximum load.
        """
        ep_group = get_ep_group().device_group
        if is_profile:
            self.rearrange(is_profile=True)
            return

        if is_dummy:
            # Do not record load metrics for dummy steps
            for eplb_model_state in self.model_states.values():
                eplb_model_state.expert_load_pass.zero_()

        if (
            log_stats
            and self.expert_rearrangement_step
            % self.parallel_config.eplb_config.log_balancedness_interval
            == 0
        ):
            # Sync the expert load pass for each model (main and drafter).
            # expert_load_pass: (num_moe_layers, num_physical_experts)
            expert_load_pass_list = self._sync_load_pass()
            ep_group = get_ep_group().device_group
            for expert_load_pass, eplb_model_state in zip(
                expert_load_pass_list, self.model_states.values()
            ):
                # num_tokens_per_rank: (num_moe_layers, num_ranks)
                num_tokens_per_rank = (
                    expert_load_pass.reshape(
                        expert_load_pass.shape[0], ep_group.size(), -1
                    )
                    .sum(dim=-1)
                    .float()
                )

                # Compute balancedness ratio:
                # for each layer:
                #   (mean load across ranks) / (max load across ranks)
                avg_tokens_tensor = num_tokens_per_rank.mean(dim=0).sum(dim=0)
                max_tokens_tensor = num_tokens_per_rank.max(dim=0).values.sum(dim=0)

                # Just to make type checker happy
                tokens_tensors: list[float] = torch.stack(
                    [avg_tokens_tensor, max_tokens_tensor]
                ).tolist()
                avg_tokens, max_tokens = tokens_tensors
                balancedness = avg_tokens / max_tokens if max_tokens > 0 else 0.0

                if ep_group.rank() == 0:
                    logger.info(
                        "EPLB step: %d for model %s: avg_tokens=%.2f, "
                        "max_tokens=%d, balancedness=%.4f, "
                        "steps until the next rearrangement: %d",
                        self.expert_rearrangement_step,
                        eplb_model_state.model_name,
                        avg_tokens,
                        max_tokens,
                        balancedness,
                        self.expert_rearrangement_step_interval
                        - self.expert_rearrangement_step,
                    )

        # Update the expert load sliding window
        if not is_dummy:
            should_record = self._should_record_current_step(log_stats=log_stats)
            for eplb_model_state in self.model_states.values():
                if should_record:
                    eplb_model_state.expert_load_window[
                        self.expert_load_window_step
                    ].copy_(eplb_model_state.expert_load_pass)
                    eplb_model_state.expert_load_pass.zero_()

            if should_record:
                self.expert_load_window_step += 1
                if self.expert_load_window_step >= self.expert_load_window_size:
                    self.expert_load_window_step = 0

        # Step the expert rearrangement step
        # Note that even if this is a dummy step, we still increment the
        # rearrangement step and perform rearrangement to ensure all ranks are
        # performing collective communication.
        self.expert_rearrangement_step += 1

        if self.is_async:
            # Run _move_to_workspace if all ranks have finished transferring the
            # new weights to the intermediate buffer
            for eplb_model_state in self.model_states.values():
                # rebalanced must remain consistent amongst all ranks otherwise the
                # all_reduce in _all_ranks_result_ready will hang
                if eplb_model_state.rebalanced and self._all_ranks_result_ready(
                    eplb_model_state
                ):
                    _move_to_workspace(
                        model_state=eplb_model_state,
                        ep_rank=ep_group.rank(),
                    )

        if self.expert_rearrangement_step >= self.expert_rearrangement_step_interval:
            if self.is_async and any(
                eplb_model_state.rebalanced
                for eplb_model_state in self.model_states.values()
            ):
                # Still performing asynchronous rearrangement; update
                # should_record (step > step_interval, so always True) and
                # bail out before the step counter is reset.
                self._update_layer_should_record(log_stats=log_stats)
                return
            self.expert_rearrangement_step = 0
            self.rearrange()

        self._update_layer_should_record(log_stats=log_stats)