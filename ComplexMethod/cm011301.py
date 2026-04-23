def _warmup_p2p(
        self,
        stages: list[_PipelineStageBase],
        has_backward: bool,
        p2p_done: bool,
    ) -> None:
        """Run the P2P warm-up protocol for the given stages.

        For ``PipelineStage`` instances this executes the forward/backward vote
        protocol (which warms up 2-rank sub-communicators) and sets each
        stage's ``_inference_mode``.  For other stage types it falls back to
        the legacy ``_get_init_p2p_neighbors_ops`` + ``_batch_p2p`` path.

        Args:
            stages: The pipeline stages owned by this rank.
            has_backward: Whether the schedule includes a backward pass.
            p2p_done: ``True`` if P2P neighbours have already been initialised
                (avoids redundant init on eval↔train mode switches).
        """
        if all(isinstance(stage, PipelineStage) for stage in stages):
            acc: torch.Tensor | None = None
            for stage in cast(list[PipelineStage], stages):
                acc = stage._warmup_forward_vote(has_backward, received_acc=acc)
            result: torch.Tensor | None = acc
            determined_mode: InferenceMode | None = None
            for stage in reversed(cast(list[PipelineStage], stages)):
                result = stage._warmup_backward_result(received_result=result)
                if result is None:
                    raise RuntimeError("P2P warm-up voting failed")
                determined_mode = (
                    InferenceMode.STATIC
                    if result.item() == 1
                    else InferenceMode.DYNAMIC
                )
                stage._inference_mode = determined_mode
            logger.debug(
                "Rank determined inference_mode=%s for %d stage(s)",
                determined_mode.value if determined_mode else "None",
                len(stages),
            )
        elif not p2p_done:
            all_ops: list[dist.P2POp] = []
            for stage in stages:
                all_ops.extend(stage._get_init_p2p_neighbors_ops())
            _wait_batch_p2p(_batch_p2p(all_ops))