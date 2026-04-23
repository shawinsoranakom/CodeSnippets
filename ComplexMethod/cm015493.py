def _sync_tp_grads(
        self,
        tp_fsdp_model: FSDP,
        tp_pg: dist.ProcessGroup,
        param_name_to_numel: dict[str, int],
        non_sharded_param_names: list[str],
    ) -> None:
        """
        Syncs the tensor parallel parameters' gradients following the data
        parallel paradigm where gradients are averaged over ranks (in this
        case, the ones in the tensor parallel process group).
        """
        tp_world_size = tp_pg.size()
        fsdp_world_size = self.world_size // tp_world_size
        if not (
            type(tp_fsdp_model) is FSDP
            and len([m for m in tp_fsdp_model.modules() if type(m) is FSDP]) == 1
        ):
            raise AssertionError(
                "The following logic assumes a single top-level-only FSDP wrapping "
                "the model with TP already applied"
            )
        for flat_param in tp_fsdp_model.params:
            splits = tuple(param_name_to_numel.values())
            # Create a mask over the gradient elements to manually reduce
            unsharded_size = torch.Size([flat_param.numel() * fsdp_world_size])
            unsharded_zeros = torch.zeros(unsharded_size, device=flat_param.device)
            per_param_masks = unsharded_zeros.split(splits)
            for param_idx, param_name in enumerate(
                param_name_to_numel.keys()
            ):  # assumes fixed order
                if param_name not in non_sharded_param_names:
                    per_param_masks[param_idx][:] = 1
            unsharded_mask = (
                torch.cat(per_param_masks).contiguous().type(torch.BoolTensor)
            )
            sharded_mask = unsharded_mask.chunk(fsdp_world_size)[
                self.rank // tp_world_size
            ]
            grad_device = flat_param.grad.device
            grad = flat_param.grad.detach().clone().to(self.rank)
            dist.all_reduce(grad, op=dist.ReduceOp.SUM, group=tp_pg)
            grad = grad.to(grad_device)
            flat_param.grad[~sharded_mask] = grad[~sharded_mask]
            # Average *all* gradient elements to match the FSDP only semantics
            flat_param.grad /= tp_world_size