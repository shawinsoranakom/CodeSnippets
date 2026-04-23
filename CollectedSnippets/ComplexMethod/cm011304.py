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
        Will go through all the microbatches according to the 1F1B schedule.

        Args:
            microbatches: list of microbatch args.
            return_outputs: whether to return the outputs from the last stage.
        """
        arg_mbs, kwarg_mbs = self._check_inputs(arg_mbs, kwarg_mbs, target_mbs, losses)
        maybe_first_target = target_mbs[0] if target_mbs is not None else None
        self._initialize_stage(arg_mbs[0], kwarg_mbs[0], maybe_first_target)

        # Last stage has 1 warmup, second-to-last 2 warmups, ...
        # first stage `num_stages` warmups
        warmup_chunks = min(
            self._n_microbatches,
            self._num_stages - self._stage.stage_index,
        )

        # Chunk counters
        fwd_mb_index = 0
        bwd_mb_index = 0

        # Warmup phase
        send_work: list[dist.Work] = []
        fwd_sends = []
        for _ in range(warmup_chunks):
            # Receive activations
            fwd_recvs = self._stage.get_fwd_recv_ops(fwd_mb_index)
            _wait_batch_p2p(_batch_p2p(fwd_recvs, desc="fwd_recv"))

            # Compute
            output = self._stage.forward_one_chunk(
                fwd_mb_index,
                arg_mbs[fwd_mb_index],
                kwarg_mbs[fwd_mb_index],
                save_forward_output=return_outputs,
            )  # type: ignore[index]

            # Clear previous chunk's forward sends (hopefully they have well
            # finished, otherwise, we are heavily communication bound, in which
            # case it doesn't create a lot of benefit to compute next chunk
            # eagerly either)
            _wait_batch_p2p(send_work)

            # Send activations
            fwd_sends = self._stage.get_fwd_send_ops(fwd_mb_index)
            if fwd_mb_index != warmup_chunks - 1:
                # Safe to fire
                send_work = _batch_p2p(fwd_sends, desc="fwd_send")
            # otherwise:
            #   The last forward send is left for fuse with first 1B in 1B1F below

            # Compute loss
            self._maybe_compute_loss(self._stage, output, target_mbs, fwd_mb_index)
            fwd_mb_index += 1

        # Now we should have send ops left over, to be fused with first 1B of 1B1F phase below.

        # 1B1F phase
        while True:  # Don't worry, we have a break inside
            # We actually do 1B first as the `1B1F` name indicates, so prepare its recv ops
            bwd_recvs = self._stage.get_bwd_recv_ops(bwd_mb_index)

            # Now, we need to fire the fwd_sends and bwd_recvs together
            _wait_batch_p2p(_batch_p2p(fwd_sends + bwd_recvs, desc="fwd_send_bwd_recv"))

            # Backward one chunk
            loss = self._maybe_get_loss(self._stage, bwd_mb_index)
            self._stage.backward_one_chunk(
                bwd_mb_index,
                loss=loss,
                last_backward=bwd_mb_index == self._n_microbatches - 1,
            )

            # Get the bwd send ops, but don't fire, to be fused with the 1F below
            bwd_sends = self._stage.get_bwd_send_ops(bwd_mb_index)
            bwd_mb_index += 1

            if fwd_mb_index == self._n_microbatches:
                # We are done with 1B1F, so break with some left-over bwd_sends
                break

            # We prepare 1F of the `1B1F`
            fwd_recvs = self._stage.get_fwd_recv_ops(fwd_mb_index)

            # Fuse it with bwd_sends above
            _wait_batch_p2p(_batch_p2p(bwd_sends + fwd_recvs, desc="bwd_send_fwd_recv"))

            # Now do the fwd
            output = self._stage.forward_one_chunk(
                fwd_mb_index,
                arg_mbs[fwd_mb_index],
                kwarg_mbs[fwd_mb_index],
                save_forward_output=return_outputs,
            )  # type: ignore[index]

            # Compute loss
            self._maybe_compute_loss(self._stage, output, target_mbs, fwd_mb_index)

            # Get the fwd send ops, but don't fire, leave it for the next iter (wrap-around)
            fwd_sends = self._stage.get_fwd_send_ops(fwd_mb_index)
            fwd_mb_index += 1

        # Remember we still have some bwd_sends left over after the break? Now it is time to fire it
        send_work = _batch_p2p(bwd_sends, desc="bwd_send")

        # Cooldown
        while bwd_mb_index < self._n_microbatches:
            # prepare bwd recv ops
            bwd_recvs = self._stage.get_bwd_recv_ops(bwd_mb_index)
            _wait_batch_p2p(_batch_p2p(bwd_recvs, desc="bwd_recv"))

            # Backward one chunk
            loss = self._maybe_get_loss(self._stage, bwd_mb_index)
            self._stage.backward_one_chunk(
                bwd_mb_index,
                loss=loss,
                last_backward=bwd_mb_index == self._n_microbatches - 1,
            )

            # Clear previous chunk's backward sends (hopefully they have well finished)
            _wait_batch_p2p(send_work)

            # Get the bwd send ops, fire it
            bwd_sends = self._stage.get_bwd_send_ops(bwd_mb_index)
            send_work = _batch_p2p(bwd_sends, desc="bwd_send")
            bwd_mb_index += 1

        # Wait for the last backward send to finish
        _wait_batch_p2p(send_work)

        # Return losses if there is a container passed in
        self._update_losses(self._stage, losses)

        self._stage.perform_reduce_grad(self._n_microbatches if self.scale_grads else 1)