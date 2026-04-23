def distributed_concat(tensor: Any, num_total_examples: int | None = None) -> Any:
    try:
        if isinstance(tensor, (tuple, list)):
            return type(tensor)(distributed_concat(t, num_total_examples) for t in tensor)
        if isinstance(tensor, Mapping):
            return type(tensor)({k: distributed_concat(t, num_total_examples) for k, t in tensor.items()})
        tensor = atleast_1d(tensor).contiguous()
        output_tensors = [tensor.clone() for _ in range(dist.get_world_size())]
        dist.all_gather(output_tensors, tensor)
        concat = torch.cat(output_tensors, dim=0)

        # truncate the dummy elements added by SequentialDistributedSampler
        if num_total_examples is not None:
            concat = concat[:num_total_examples]
        return concat
    except AssertionError:
        raise AssertionError("Not currently using distributed training")