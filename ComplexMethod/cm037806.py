def _finalize(
        self,
        output: torch.Tensor,
        fused_expert_output: torch.Tensor,
        topk_weights: torch.Tensor,
        topk_ids: torch.Tensor,
        apply_router_weight_on_input: bool,
        weight_and_reduce_impl: mk.TopKWeightAndReduce,
        do_async: bool,
    ) -> Callable | None:
        a2a_idx = dbo_current_ubatch_id()
        handle = self.handles[a2a_idx]
        assert handle is not None

        # fused_expert_output can have 0 tokens - This happens when none of the
        # tokens from the all2all reach this EP rank.
        if fused_expert_output.numel() != 0:
            if isinstance(weight_and_reduce_impl, TopKWeightAndReduceDelegate):
                weight_and_reduce_impl = TopKWeightAndReduceContiguous()
            fused_expert_output = weight_and_reduce_impl.apply(
                output=None,
                fused_expert_output=fused_expert_output,
                topk_weights=topk_weights,
                topk_ids=topk_ids,
                apply_router_weight_on_input=apply_router_weight_on_input,
            )
        previous_event = dbo_get_previous_event(self.buffer.capture)
        dbo_yield_and_switch_from_compute_to_comm()
        assert fused_expert_output.dtype == torch.bfloat16, (
            f"Expected fused_expert_output bfloat16, got {fused_expert_output.dtype}"
        )
        combined_x, _, event = self.buffer.combine(
            # HT combine only supports BF16
            x=fused_expert_output,
            handle=handle,
            topk_weights=None,
            config=self._get_combine_config(),
            previous_event=previous_event,
            async_finish=do_async and not dbo_enabled(),
            allocate_on_comm_stream=False,
        )

        dbo_switch_to_compute()

        if do_async:

            def _receiver():
                if event.event is not None:
                    event.current_stream_wait()
                dbo_switch_to_comm()
                # Respect inplace outputs.
                output.copy_(combined_x, non_blocking=True)

                # TODO(lucas): refactor the modular kernel so this will be
                # handled there
                dbo_yield_and_switch_from_comm_to_compute()

            return _receiver
        else:
            # TODO(lucas): support this case with the refactored modular kernel
            assert not dbo_enabled()
            # Respect inplace outputs.
            output.copy_(combined_x, non_blocking=True)
            return None