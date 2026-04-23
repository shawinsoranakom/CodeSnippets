def _step_microbatches(
        self,
        arg_mbs: list | None = None,
        kwarg_mbs: list | None = None,
        target_mbs: list | None = None,
        losses: list | None = None,
        return_outputs: bool = True,
    ):
        """
        Run one iteration of the pipeline schedule with list of microbatches.
        Will go through all the microbatches according to the GPipe schedule.

        Args:
            microbatches: list of microbatch args.
            return_outputs: whether to return the outputs from the last stage.
        """
        arg_mbs, kwarg_mbs = self._check_inputs(arg_mbs, kwarg_mbs, target_mbs, losses)
        maybe_first_target = target_mbs[0] if target_mbs is not None else None
        self._initialize_stage(arg_mbs[0], kwarg_mbs[0], maybe_first_target)

        # Delay send waits
        fwd_sends_to_wait: list[list[dist.Work]] = []

        # Run microbatches
        for i in range(self._n_microbatches):
            with record_function(f"Forward {i}"):
                ops = self._stage.get_fwd_recv_ops(i)
                works = _sorted_batch_p2p(ops, desc="fwd_recv")
                for work in works.values():
                    _wait_batch_p2p(work)

                output = self._stage.forward_one_chunk(
                    i, arg_mbs[i], kwarg_mbs[i], save_forward_output=return_outputs
                )  # type: ignore[index]

                ops = self._stage.get_fwd_send_ops(i)
                works = _sorted_batch_p2p(ops, desc="fwd_send")
                fwd_sends_to_wait.extend(works.values())

            logger.debug("[%s] Forwarded microbatch %s", self._stage.stage_index, i)

            self._maybe_compute_loss(self._stage, output, target_mbs, i)

        # Wait for all forward sends to finish
        # This should not have performance impact because by the time the first
        # backward arrives all the forward sends should have been finished.
        for work in fwd_sends_to_wait:
            _wait_batch_p2p(work)

        # Run backward
        # Delay send waits
        bwd_sends_to_wait: list[list[dist.Work]] = []
        for i in range(self._n_microbatches):
            with record_function(f"Backward {i}"):
                ops = self._stage.get_bwd_recv_ops(i)
                works = _sorted_batch_p2p(ops, desc="bwd_recv")
                for work in works.values():
                    _wait_batch_p2p(work)

                loss = self._maybe_get_loss(self._stage, i)
                self._stage.backward_one_chunk(
                    i,
                    loss=loss,
                    last_backward=i == self._n_microbatches - 1,
                )

                ops = self._stage.get_bwd_send_ops(i)
                works = _sorted_batch_p2p(ops, desc="bwd_send")
                bwd_sends_to_wait.extend(works.values())

            logger.debug("[%s] Backwarded microbatch %s", self._stage.stage_index, i)

        # Wait for all backward sends to finish
        for work in bwd_sends_to_wait:
            _wait_batch_p2p(work)

        # Update losses if there is a container passed in
        self._update_losses(self._stage, losses)

        self._stage.perform_reduce_grad(self._n_microbatches if self.scale_grads else 1)