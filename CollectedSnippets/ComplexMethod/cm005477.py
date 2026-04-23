def shard_tensor(
        self, param: torch.Tensor, tensor_idx: int | None = None, device=None, dtype=None
    ) -> torch.Tensor:
        global_num_experts = self.empty_param.shape[0]
        if global_num_experts % self.device_mesh.size() != 0:
            raise ValueError(
                f"Global number of experts must be divisible by number of devices: {global_num_experts} % {self.device_mesh.size()} != 0"
            )
        local_num_experts = global_num_experts // self.device_mesh.size()
        shard_size = local_num_experts
        start = self.rank * shard_size
        end = (self.rank + 1) * shard_size
        # special case we don't "shard" just send this entire tensor to the correct rank.
        shape = param.get_shape() if not isinstance(param, torch.Tensor) else param.shape
        if tensor_idx is not None and start <= tensor_idx < end:
            # this tensor does need to be materialized on this device:
            return param[:].to(device=device)
        elif tensor_idx is None:  # a bias or a weight, but already merged
            return param[start:end].to(device=device, dtype=dtype)
        elif len(shape) >= 1 and tensor_idx is not None:
            return None
        else:  # bias case
            return param[:].to(device=device, dtype=dtype)