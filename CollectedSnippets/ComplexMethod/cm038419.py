def isend_tensor_dict(
        self,
        tensor_dict: dict[str, torch.Tensor | Any],
        dst: int | None = None,
        all_gather_group: "GroupCoordinator | None" = None,
        all_gather_tensors: dict[str, bool] | None = None,
    ) -> list[Handle]:
        if self.world_size <= 1:
            return []

        if dst is None:
            dst = (self.rank_in_group + 1) % self.world_size
        assert dst < self.world_size, f"Invalid dst rank ({dst})"

        if self.use_cpu_custom_send_recv:
            if self.device_communicator is None:
                raise ValueError("No device communicator found")
            # custom device communicator path is synchronous
            self.device_communicator.send_tensor_dict(  # type: ignore
                tensor_dict, dst
            )
            return []

        all_gather_size = 1 if all_gather_group is None else all_gather_group.world_size
        all_gather_rank = (
            0 if all_gather_group is None else all_gather_group.rank_in_group
        )

        group = self.device_group
        metadata_group = self.cpu_group

        metadata_list, tensor_list = _split_tensor_dict(tensor_dict)
        self.send_object(metadata_list, dst=dst)

        tensor_keys = [k for k, v in tensor_dict.items() if isinstance(v, torch.Tensor)]
        assert len(tensor_keys) == len(tensor_list)

        handles: list[Handle] = []
        for key, tensor in zip(tensor_keys, tensor_list):
            if tensor.numel() == 0:
                continue

            if self._should_use_all_gather(
                key, tensor.numel(), all_gather_group, all_gather_tensors
            ):
                tensor = tensor.reshape(all_gather_size, -1)[all_gather_rank]

            comm_group = metadata_group if tensor.is_cpu else group
            handle = torch.distributed.isend(
                tensor, dst=self.ranks[dst], group=comm_group
            )
            if tensor.is_cuda:
                tensor.record_stream(torch.cuda.current_stream(tensor.device))
            handles.append(handle)

        return handles