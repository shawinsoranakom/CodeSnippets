def _forward_metadata_inference(
        self,
        args: tuple[torch.Tensor, ...] | _StageForwardMeta | None,
        kwargs: dict[str, Any] | None = None,
        has_backward: bool = False,
    ) -> _StageForwardMeta | None:
        """Run forward metadata inference (Stage 0 → N).

        Args:
            args: Real tensors (first stage), ``_StageForwardMeta``
                (same-rank), or ``None`` (cross-rank P2P).
            kwargs: Keyword arguments forwarded to the submodule.
            has_backward: Whether backward inference follows.

        Returns:
            ``_StageForwardMeta`` for the next stage, or ``None`` if sent via P2P.
        """
        kwargs = kwargs or {}

        # === RECEIVE: Get input metadata and create meta tensors ===
        if self.is_first:
            # First stage: extract metadata from real tensors
            if args is None or isinstance(args, _StageForwardMeta):
                raise PipeliningMetadataError(
                    f"Stage {self.stage_index}: First stage requires real tensors, "
                    f"got {type(args).__name__}."
                )
            tensor_args = validate_and_normalize_to_tuple(args)
            assert tensor_args is not None  # noqa: S101
            self._stage_meta.inputs = extract_tensor_metas(tensor_args)
            inference_args = tuple(self._to_tensor(a) for a in tensor_args)
        elif self._is_same_rank(self.stage_index - 1):
            # Same-rank: _StageForwardMeta passed via argument
            if not isinstance(args, _StageForwardMeta):
                raise PipeliningMetadataError(
                    f"Stage {self.stage_index}: Expected _StageForwardMeta from same-rank "
                    f"previous stage, got {type(args).__name__}."
                )
            self._stage_meta.inputs = args.forward_metas
            inference_args = tuple(self._to_tensor(m) for m in args.forward_metas)
        else:
            # Cross-rank: receive _StageForwardMeta via P2P
            recv_meta = self._recv_meta(self.stage_index - 1)
            if not isinstance(recv_meta, _StageForwardMeta):
                raise PipeliningMetadataError(
                    f"Stage {self.stage_index}: Expected _StageForwardMeta from P2P, "
                    f"got {type(recv_meta).__name__}."
                )
            self._stage_meta.inputs = recv_meta.forward_metas
            inference_args = tuple(self._to_tensor(m) for m in recv_meta.forward_metas)

        inference_kwargs = {
            k: self._to_tensor(v) if isinstance(v, torch.Tensor) else v
            for k, v in kwargs.items()
        }

        # Isolate metadata inference from user's grad context.
        # has_backward → enable_grad() so backward tracing sees grad_fn;
        # no backward → no_grad() for cross-rank consistency.
        ctx = torch.enable_grad() if has_backward else torch.no_grad()
        with ctx:
            outputs = self._compute_outputs(
                *inference_args, module=self.submod, **inference_kwargs
            )

        # Normalize outputs to tuple
        outputs = validate_and_normalize_to_tuple(outputs)

        self._stage_meta.outputs = extract_tensor_metas(outputs)

        # Store for backward metadata inference (always, even during eval)
        fwd_kwargs_tensors = tuple(
            v for v in flatten_args(inference_kwargs) if isinstance(v, torch.Tensor)
        )
        self._fwd_outputs_for_bwd_meta = outputs
        self._fwd_inputs_for_bwd_meta = inference_args
        self._fwd_kwargs_tensors_for_bwd_meta = fwd_kwargs_tensors

        # === SEND: Pass output metadata to next stage ===
        if self._stage_meta.outputs is None:
            raise PipeliningMetadataError(
                f"Stage {self.stage_index}: output metadata is required for forward inference."
            )
        fwd_meta = _StageForwardMeta(forward_metas=self._stage_meta.outputs)

        if self.is_last or self._is_same_rank(self.stage_index + 1):
            # Same-rank or last: return for caller to pass
            return fwd_meta
        else:
            # Cross-rank: send via P2P
            self._send_meta(fwd_meta, self.stage_index + 1)
            return None