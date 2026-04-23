def _offload_tensor(self, x, memo, non_blocking=False):
        """
        Deep copy a PyTorch tensor with optimized storage handling.

        This method creates a CPU copy of a tensor while applying memory optimizations
        like sharing and pinning based on the StateDictStager configuration.

        Args:
            x: The tensor to copy
            memo: Memo dictionary for tracking already copied objects
            non_blocking: Whether to perform non-blocking copies where possible

        Returns:
            A CPU copy of the tensor with optimized storage
        """
        # if data_ptr is not 0, we allocate a new storage below. so we can skip
        # memory allocation by using [] for size.
        y = x.new_empty([] if x.data_ptr() != 0 else x.size(), device="cpu")

        # Store in memo dict early to handle recursive references
        d = id(x)
        memo[d] = y

        if type(x) is torch.Tensor or x.data_ptr() != 0:
            # Get the untyped storage
            untyped_storage = x.untyped_storage()
            storage_id = id(untyped_storage)

            # Check if this storage has already been staged in this deepcopy operation
            # This handles the case where different tensors share the same storage
            # (e.g., FSDP state_dict where norm.weight and norm_weight reference same storage)
            # PyTorch caches untyped_storage() calls, so same storage -> same id
            if storage_id in memo:
                copied_storage = memo[storage_id]
            else:
                # Storage not seen before in this operation, stage it
                copied_storage = self._stage_untyped_storage(
                    untyped_storage, non_blocking=non_blocking
                )
                # Add to memo to avoid re-staging if we see this storage again
                memo[storage_id] = copied_storage

            # Set the tensor data using the staged storage
            y.set_(copied_storage, x.storage_offset(), x.size(), x.stride())

        # Copy any attributes the tensor might have
        if hasattr(x, "__dict__"):
            for attr_name, attr_value in x.__dict__.items():
                setattr(
                    y,
                    attr_name,
                    self.deepcopy_with_tensor_offload(
                        attr_value, memo, non_blocking=non_blocking
                    ),
                )

        if hasattr(x, "__slots__"):
            for slot in x.__slots__:
                if hasattr(x, slot):
                    setattr(
                        y,
                        slot,
                        self.deepcopy_with_tensor_offload(
                            getattr(x, slot), memo, non_blocking=non_blocking
                        ),
                    )

        return y