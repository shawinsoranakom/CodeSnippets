def recv_tensor_dict(
        self,
        src: int | None = None,
        all_gather_group: Optional["GroupCoordinator"] = None,
        all_gather_tensors: dict[str, bool] | None = None,
    ) -> dict[str, torch.Tensor | Any] | None:
        if self.world_size == 1:
            return None

        if src is None:
            src = (self.rank_in_group - 1) % self.world_size
        assert src < self.world_size

        recv_metadata_list = self.tcp_store_group.recv_obj(src)
        tensor_dict = {}
        for key, value in recv_metadata_list:
            if isinstance(value, TensorMetadata):
                tensor = torch.empty(value.size, dtype=value.dtype, device=value.device)
                if tensor.numel() > 0:
                    if self.device_communicator and tensor.is_cuda:
                        tensor = self.device_communicator.recv(
                            tensor.size(), tensor.dtype, src
                        )
                    else:
                        tensor = self.tcp_store_group.recv(tensor, src)
                tensor_dict[key] = tensor
            else:
                tensor_dict[key] = value
        return tensor_dict