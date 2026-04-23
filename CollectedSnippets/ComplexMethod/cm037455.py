def __call__(
        self, dtype: str, shape: tuple[int, ...], meta: dict[str, Any]
    ) -> torch.Tensor:
        """Retrieve a tensor from torch.multiprocessing.Queue.

        Uses a drain-and-buffer pattern: drains all available tensors from
        the queue, buffering them, until the requested tensor is found.
        Works for CUDA and CPU.
        """

        # Create lookup key from handle
        sender_id: str = meta["sender_id"]
        message_id: int = meta["message_id"]
        tensor_id: int = meta["tensor_id"]

        # Drain all available tensors. We save them regardless if this is
        # the one we're waiting for as they may arrive out of order from
        # multiple producers.
        while True:
            sender = self._tensor_buffers.get(sender_id)
            if sender is not None:
                tensors = sender.tensors
                tensor = tensors.get(message_id, {}).pop(tensor_id, None)
                if tensor is not None:
                    if sender.current_message_id != message_id:
                        while tensors and (mid := next(iter(tensors))) < message_id:
                            if sender.tensors.pop(mid):
                                logger.warning(
                                    "Discarding %d stale tensors from sender %s",
                                    sender_id,
                                )
                        sender.current_message_id = message_id
                    logger.debug(
                        "Received tensor %s from sender %s for (shape=%s, device=%s) "
                        "via IPC queue (shared memory)",
                        (message_id, tensor_id),
                        sender_id,
                        tensor.shape,
                        tensor.device,
                    )
                    return tensor

            ipc_data: TensorIpcData = self.queue.get(timeout=10.0)

            # Store tensor
            sender = self._tensor_buffers[ipc_data.sender_id]
            if sender.current_message_id > ipc_data.message_id:
                logger.warning(
                    "Ignoring stale tensor from sender %s", ipc_data.sender_id
                )
                continue

            sender.tensors.setdefault(ipc_data.message_id, {})[ipc_data.tensor_id] = (
                ipc_data.tensor
            )