def broadcast_tensor_dict(
        self,
        tensor_dict: dict[str, torch.Tensor | Any] | None = None,
        src: int = 0,
        group: ProcessGroup | None = None,
        metadata_group: ProcessGroup | None = None,
    ) -> dict[str, torch.Tensor | Any] | None:
        if self.world_size == 1:
            return tensor_dict

        if self.rank_in_group == src:
            assert isinstance(tensor_dict, dict), (
                f"Expecting a dictionary, got {type(tensor_dict)}"
            )
            metadata_list, tensor_list = _split_tensor_dict(tensor_dict)
        else:
            metadata_list = None
            tensor_list = []

        recv_metadata_list: list[tuple[str, Any]] = self.tcp_store_group.broadcast_obj(
            metadata_list, src
        )

        if self.rank_in_group != src:
            tensor_dict = {}
            for key, value in recv_metadata_list:
                if isinstance(value, TensorMetadata):
                    tensor = torch.empty(
                        value.size, dtype=value.dtype, device=value.device
                    )
                    tensor_list.append(tensor)
                    tensor_dict[key] = tensor
                else:
                    tensor_dict[key] = value

        for tensor in tensor_list:
            if tensor.numel() == 0:
                continue
            if self.device_communicator and tensor.is_cuda:
                tensor.copy_(self.device_communicator.broadcast(tensor, src))
            else:
                tensor.copy_(self.tcp_store_group.broadcast(tensor, src))

        return tensor_dict