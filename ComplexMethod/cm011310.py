def _prepare_schedule_with_comms(
        self,
        actions: dict[int, list[_Action | None]],
        format: str = "compute_only",
    ):
        """
        Given an in-memory representation for a simple compute-only schedule, lower it to a complex schedule including
        communication actions.  Stores the schedule in self, and must be called before running step_mo()
        """
        # validate the provided actions are valid and overrides the default stage_index_to_group_rank
        super()._validate_and_set_stage_mapping(actions)

        self.pipeline_order_with_comms: dict[int, list[_Action]] = {}
        if format == "compute_comms":
            for rank in actions:
                self.pipeline_order_with_comms[rank] = []
                for action in actions[rank]:
                    if action is None:
                        raise AssertionError(
                            f"Expected action to be not None, got {type(action)}"
                        )
                    self.pipeline_order_with_comms[rank].append(action)
            # TODO what level of validation should we offer for compute+comms schedule?
        elif format == "compute_only":
            # Validate that the schedule does not have comms already added to it
            for rank, action_list in actions.items():
                for i, action in enumerate(action_list):
                    if action is not None:
                        if not action.is_compute_op:
                            raise ValueError(
                                f"Expected compute-only schedule but found communication action "
                                f"'{action}' at rank {rank}, position {i}. "
                                f"Communication actions (e.g. SEND_F, RECV_F, etc.) "
                                f"should not be present when format='compute_only'."
                            )

            # Perform schedule lowering
            for rank in actions:
                self.pipeline_order_with_comms[rank] = _add_unshard_reshard(
                    actions[rank]
                )
                self.pipeline_order_with_comms[rank] = _add_reduce_grad(  # type: ignore[assignment]
                    self.pipeline_order_with_comms[rank],  # type: ignore[arg-type]
                    self._n_microbatches,
                )

            self.pipeline_order_with_comms = _add_send_recv(
                self.pipeline_order_with_comms,
                stage_to_rank=lambda s: self.stage_index_to_group_rank[s],
                num_stages=self._num_stages,
            )
        else:
            raise NotImplementedError(f"{format=} is not implemented")