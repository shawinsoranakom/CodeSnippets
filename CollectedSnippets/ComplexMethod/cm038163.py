def weight_loader(
        self,
        param: nn.Parameter,
        loaded_weight: torch.Tensor,
        weight_name: str,
        param_name: str,
    ):
        tp_rank = get_tensor_model_parallel_rank()
        param_data = param.data
        shard_size = self.intermediate_size
        shard = slice(tp_rank * shard_size, (tp_rank + 1) * shard_size)
        # DBRX uses GLU for each experts.
        # GLU has 3 linear layers: w1, v1 and w2.
        if weight_name.endswith("w1"):
            if param_name.endswith("weight"):
                loaded_weight = torch.reshape(
                    loaded_weight,
                    [-1, self.intermediate_size * self.tp_size, self.d_model],
                )
                param_data[:, 0:shard_size, :] = loaded_weight[:, shard, :]
            elif param_name.endswith("weight_scale"):
                param_data[:, 0] = loaded_weight
            else:
                param_data = loaded_weight
        if weight_name.endswith("v1"):
            if param_name.endswith("weight"):
                loaded_weight = torch.reshape(
                    loaded_weight,
                    [-1, self.intermediate_size * self.tp_size, self.d_model],
                )
                param_data[:, shard_size : 2 * shard_size, :] = loaded_weight[
                    :, shard, :
                ]
            elif param_name.endswith("weight_scale"):
                param_data[:, 1] = loaded_weight
            else:
                param_data[:] = loaded_weight
        if weight_name.endswith("w2"):
            if param_name.endswith("weight"):
                loaded_weight = torch.reshape(
                    loaded_weight,
                    [-1, self.intermediate_size * self.tp_size, self.d_model],
                ).transpose(1, 2)
                param_data[:] = loaded_weight[:, :, shard]
            else:
                param_data[:] = loaded_weight