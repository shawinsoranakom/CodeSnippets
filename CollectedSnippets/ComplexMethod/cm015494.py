def _get_grads_as_flattened(
        self,
        model: FSDP,
        uses_tp: bool,
        param_name_to_numel: dict[str, int],
        param_name_to_sharding_info: dict[str, tuple[torch.Size, int]],
        tp_pg: dist.ProcessGroup | None,
        fsdp_pg: dist.ProcessGroup | None,
        sharded_param_names: list[str] | None,
    ) -> torch.Tensor:
        """
        Returns all unsharded gradients as a single flattened tensor. This
        returns the same value on all ranks.
        """
        local_grads_as_flattened = (
            torch.cat(
                [
                    (
                        torch.flatten(param.grad)
                        if param.grad is not None
                        else torch.zeros_like(torch.flatten(param))
                    )
                    for param in model.parameters()
                ]
            )
            .contiguous()
            .to(self.rank)
        )
        all_grads_as_flattened = torch.cat(
            [torch.empty_like(local_grads_as_flattened) for _ in range(fsdp_pg.size())]
        ).contiguous()
        dist.all_gather_into_tensor(
            all_grads_as_flattened, local_grads_as_flattened, group=fsdp_pg
        )
        if not uses_tp:
            return all_grads_as_flattened
        splits = tuple(param_name_to_numel.values())
        all_grads_per_param = list(all_grads_as_flattened.split(splits))
        for param_idx, param_name in enumerate(
            param_name_to_numel.keys()
        ):  # assumes fixed order
            if param_name in sharded_param_names:
                local_tensor_size = list(param_name_to_sharding_info[param_name][0])
                sharding_dim = param_name_to_sharding_info[param_name][1]
                local_tensor_size[sharding_dim] //= tp_pg.size()
                local_tensor = all_grads_per_param[param_idx].view(*local_tensor_size)
                local_tensors = [
                    torch.empty_like(local_tensor) for _ in range(tp_pg.size())
                ]
                dist.all_gather(local_tensors, local_tensor, group=tp_pg)
                all_grads_per_param[param_idx] = torch.cat(
                    local_tensors, dim=sharding_dim
                ).reshape(-1)
        return torch.cat(all_grads_per_param).contiguous()