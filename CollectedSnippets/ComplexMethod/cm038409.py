def send_tensor_dict(
        self,
        tensor_dict: dict[str, torch.Tensor | Any],
        dst: int | None = None,
        all_gather_group: Optional["GroupCoordinator"] = None,
        all_gather_tensors: dict[str, bool] | None = None,
    ) -> dict[str, torch.Tensor | Any] | None:
        if self.world_size == 1:
            return tensor_dict

        if dst is None:
            dst = (self.rank_in_group + 1) % self.world_size
        assert dst < self.world_size

        metadata_list, tensor_list = _split_tensor_dict(tensor_dict)
        self.tcp_store_group.send_obj(metadata_list, dst)

        for tensor in tensor_list:
            if tensor.numel() == 0:
                continue
            if self.device_communicator and tensor.is_cuda:
                self.device_communicator.send(tensor, dst)
            else:
                self.tcp_store_group.send(tensor, dst)

        return None