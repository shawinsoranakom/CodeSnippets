def smp_gather(tensor):
        if isinstance(tensor, (list, tuple)):
            return type(tensor)(smp_gather(t) for t in tensor)
        elif isinstance(tensor, dict):
            return type(tensor)({k: smp_gather(v) for k, v in tensor.items()})
        elif not isinstance(tensor, torch.Tensor):
            raise TypeError(
                f"Can't gather the values of type {type(tensor)}, only of nested list/tuple/dicts of tensors."
            )
        all_tensors = smp.allgather(tensor, smp.CommGroup.DP_GROUP)
        all_tensors = [atleast_1d(t) for t in all_tensors]
        return torch.cat([t.cpu() for t in all_tensors], dim=0)