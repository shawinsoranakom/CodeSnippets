def set_local_bwd_input(
        self, next_stage_bwd_outputs: tuple[torch.Tensor | None, ...], mb_index: int
    ) -> None:
        """
        Moves 'grad input' tensors from the next stage to 'grad_output' on this stage, avoiding a copy or send/recv.
        Does not detach or set '_requires_grad'.
        Handles DTensor gradients for V-schedule local passing.
        """
        if not isinstance(next_stage_bwd_outputs, tuple):
            raise AssertionError(f"Expected tuple, got {type(next_stage_bwd_outputs)}")

        if not self.has_backward:
            raise AssertionError(
                "can't set bwd input if this stage doesn't have backward"
            )
        if self.is_last:
            raise AssertionError("can't set bwd input if this stage is last")
        recv_infos = self.grad_recv_info[mb_index]
        for info, tensor in zip(recv_infos, next_stage_bwd_outputs, strict=True):
            if tensor is None:
                continue
            if not isinstance(tensor, torch.Tensor):
                raise AssertionError(
                    f"expected tensor values as outputs from prev stage, got {type(tensor)}"
                )
            if info.is_root_arg:
                raise AssertionError(
                    "set_local_bwd_input should only be called with non-root RecvInfo"
                )

            # Extract local tensor for the buffer (handles DTensor or plain tensor)
            info.buffer = to_local_if_dtensor(tensor)