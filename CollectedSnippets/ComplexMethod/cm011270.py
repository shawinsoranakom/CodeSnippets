def _backward_metadata_inference(
        self,
        loss_fn: Callable[..., torch.Tensor] | None = None,
        target: torch.Tensor | None = None,
        received_grad_meta: _StageBackwardMeta | None = None,
    ) -> _StageBackwardMeta | None:
        """Run backward metadata inference (Stage N → 0).

        Args:
            loss_fn: Loss function (required for the last stage).
            target: Target tensor (required for the last stage).
            received_grad_meta: Grad metadata from next same-rank stage
                (V-schedule only).

        Returns:
            ``_StageBackwardMeta`` for the previous stage, or ``None`` if sent via P2P.
        """
        fwd_outputs = self._fwd_outputs_for_bwd_meta
        fwd_inputs = self._fwd_inputs_for_bwd_meta
        if fwd_outputs is None or fwd_inputs is None:
            raise PipeliningMetadataError(
                "Backward metadata inference requires forward metadata inference to run first"
            )
        kwargs_tensors = self._fwd_kwargs_tensors_for_bwd_meta or ()
        all_fwd_inputs = list(fwd_inputs) + list(kwargs_tensors)
        # Clear temporary storage early — local refs are sufficient from here
        self._fwd_outputs_for_bwd_meta = None
        self._fwd_inputs_for_bwd_meta = None
        self._fwd_kwargs_tensors_for_bwd_meta = None
        # === RECEIVE: Get output grad metadata (except last stage) ===
        if self.is_last:
            if loss_fn is None or target is None:
                raise PipeliningMetadataError(
                    f"Stage {self.stage_index}: loss_fn and target required for last stage"
                )
            inference_target = self._to_tensor(target)
            loss = loss_fn(
                fwd_outputs[0] if len(fwd_outputs) == 1 else fwd_outputs,
                inference_target,
            )
            self._stage_meta.output_grads = None
            all_input_grads = self._compute_input_grads(
                [loss],
                all_fwd_inputs,
            )
        else:
            # Non-last stage: receive grad metadata from next stage
            if self._is_same_rank(self.stage_index + 1):
                # Same-rank: _StageBackwardMeta passed via argument
                if not isinstance(received_grad_meta, _StageBackwardMeta):
                    raise PipeliningMetadataError(
                        f"Stage {self.stage_index}: Expected _StageBackwardMeta from same-rank "
                        f"next stage, got {type(received_grad_meta).__name__}."
                    )
                self._stage_meta.output_grads = received_grad_meta.backward_metas
            else:
                # Cross-rank: receive _StageBackwardMeta via P2P
                recv_meta = self._recv_meta(self.stage_index + 1)
                if not isinstance(recv_meta, _StageBackwardMeta):
                    raise PipeliningMetadataError(
                        f"Stage {self.stage_index}: Expected _StageBackwardMeta from P2P, "
                        f"got {type(recv_meta).__name__}."
                    )
                self._stage_meta.output_grads = recv_meta.backward_metas

            # === COMPUTE: Build grad_outputs and compute input grads ===
            # Extract output tensors and corresponding grad_outputs from metadata
            # Must iterate together to maintain alignment
            if self._stage_meta.output_grads is None:
                raise PipeliningMetadataError(
                    f"Stage {self.stage_index}: output_grads metadata is required for backward inference."
                )
            stage_output_grad_metas = self._stage_meta.output_grads

            filtered_fwd_outputs: list[torch.Tensor] = []
            filtered_output_grads: list[torch.Tensor | None] = []

            for idx, (fwd_out, grad_meta) in enumerate(
                zip(fwd_outputs, stage_output_grad_metas, strict=True)
            ):
                # Match _backward.py behavior: skip if output doesn't require grad AND has no grad_fn
                if not fwd_out.requires_grad:
                    if grad_meta is not None:
                        raise PipeliningMetadataError(
                            f"Stage {self.stage_index}: output {idx} requires_grad=False, "
                            f"but output_grads metadata is provided: {grad_meta}."
                        )
                    continue
                filtered_fwd_outputs.append(fwd_out)
                # For outputs that require grad, include them even if grad_meta is None
                # (runtime passes None grad_outputs to autograd.backward in this case)
                filtered_output_grads.append(
                    self._ones_from_metadata(grad_meta) if grad_meta else None
                )

            if filtered_fwd_outputs:
                all_input_grads = self._compute_input_grads(
                    filtered_fwd_outputs, all_fwd_inputs, filtered_output_grads
                )
                # Free intermediate references early
                filtered_fwd_outputs.clear()
                filtered_output_grads.clear()
                all_fwd_inputs.clear()
                # Only positional input grads flow to previous stage
            else:
                all_input_grads = tuple(None for _ in range(len(all_fwd_inputs)))

        input_grads = all_input_grads[: len(fwd_inputs)]
        self._stage_meta.input_grads = tuple(
            extract_tensor_meta(g) if isinstance(g, torch.Tensor) else None
            for g in input_grads
        )

        # === SEND: Pass input grad metadata to previous stage ===
        bwd_meta = _StageBackwardMeta(backward_metas=self._stage_meta.input_grads)

        if self.is_first or self._is_same_rank(self.stage_index - 1):
            # First rank or Same-rank: return for caller to pass
            return bwd_meta
        else:
            # Cross-rank: send via P2P
            self._send_meta(bwd_meta, self.stage_index - 1)
            return None