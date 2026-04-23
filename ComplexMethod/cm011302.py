def _initialize_pp_stages(
        self,
        stages: list[_PipelineStageBase],
        args: tuple[Any, ...] | Any,
        kwargs: dict[str, Any] | None,
        target: Any,
        fwd_initialized: bool,
        bwd_initialized: bool,
    ) -> tuple[bool, bool]:
        """Common stage initialization shared by Single and Multi schedules.

        Handles mode-change detection (eval↔train), P2P warm-up, RNG forking,
        forward / backward metadata inference, and FSDP cleanup.

        Returns the updated ``(fwd_initialized, bwd_initialized)`` flags.
        """
        # Detect eval↔train mode switch: if has_backward changed since last
        # init, re-initialize both fwd (recv buffers need different
        # requires_grad) and bwd.  p2p_done avoids redundant P2P warm-up.
        p2p_done = fwd_initialized
        if fwd_initialized and (self._has_backward != bwd_initialized):
            fwd_initialized = False
            bwd_initialized = False

        needs_fwd = not fwd_initialized
        needs_bwd = self._has_backward and not bwd_initialized

        if not needs_fwd and not needs_bwd:
            return fwd_initialized, bwd_initialized

        if needs_fwd:
            self._warmup_p2p(stages, self._has_backward, p2p_done)

        # Fork RNG so metadata inference doesn't perturb training RNG.
        devices = list(
            {
                torch.device(stage.device)
                for stage in stages
                if torch.device(stage.device).type != "cpu"
            }
        )
        with torch.random.fork_rng(devices=devices):
            if needs_fwd:
                next_stage_args: Any = None
                for stage in stages:
                    stage_args = args if stage.is_first else next_stage_args
                    next_stage_args = stage._prepare_forward_infra(
                        self._n_microbatches,
                        stage_args,
                        kwargs,
                        has_backward=self._has_backward,
                    )
                fwd_initialized = True

            if needs_bwd:
                prev_stage_grad_meta: Any = None
                for stage in reversed(stages):
                    prev_stage_grad_meta = stage._prepare_backward_infra(
                        self._n_microbatches,
                        loss_fn=self._loss_fn,
                        target=target,
                        received_grad_meta=prev_stage_grad_meta,
                    )
                bwd_initialized = True

        for stage in stages:
            if isinstance(stage, PipelineStage):
                stage._post_metadata_inference_cleanup()

        return fwd_initialized, bwd_initialized