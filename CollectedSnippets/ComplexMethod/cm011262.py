def get_bwd_send_ops(self, bwd_chunk_id: int) -> list[dist.P2POp]:
        """
        Get the gradient send ops for current stage's backward.
        Handles DTensor gradients by extracting local tensors.
        """
        if not self.has_backward or self.is_first:
            return []

        self._check_chunk_id(bwd_chunk_id)
        # Create bwd send infra lazily
        if self.grad_send_info is None:
            # Send info for input grads during backward:
            # List of destinations corresponding to input grads
            # Can be None if an input has no grad
            # `grad_send_info` is a mirror of `args_recv_info`
            self.grad_send_info = self._create_grad_send_info(self.args_recv_info[0])

        ops: list[dist.P2POp] = []
        grads_input = self.bwd_cache.pop(bwd_chunk_id)

        for grad, grad_recv_stage in zip(grads_input, self.grad_send_info, strict=True):
            if isinstance(grad, torch.Tensor) and grad_recv_stage is not None:
                # Extract local tensor if DTensor
                send_tensor = to_local_if_dtensor(grad)
                logger.debug(
                    "%s Sending gradient to Stage %s: %s",
                    self.log_prefix,
                    grad_recv_stage,
                    send_tensor.size(),
                )
                peer_global_rank = self._resolve_peer_global_rank(grad_recv_stage)
                ops.append(
                    dist.P2POp(dist.isend, send_tensor, peer_global_rank, self.group)
                )
            else:
                if grad is not None or grad_recv_stage is not None:
                    raise PipeliningMetadataError(
                        f"[{self.stage_index}] for chunk {bwd_chunk_id} has gradients {grad} "
                        f"and is expecting to send gradients to stage {grad_recv_stage}"
                    )
        return ops