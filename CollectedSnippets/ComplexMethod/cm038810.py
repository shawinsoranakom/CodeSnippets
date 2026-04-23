def weak_ref_tensors(
    tensors: torch.Tensor
    | list[torch.Tensor]
    | tuple[torch.Tensor]
    | IntermediateTensors,
) -> torch.Tensor | list[Any] | tuple[Any] | Any:
    """
    Convenience function to create weak references to tensors,
    for single tensor, list of tensors or tuple of tensors.
    """
    if isinstance(tensors, torch.Tensor):
        return weak_ref_tensor(tensors)
    if isinstance(tensors, list):
        return [weak_ref_tensor(t) for t in tensors]
    if isinstance(tensors, tuple):
        return tuple(weak_ref_tensor(t) for t in tensors)

    # For IntermediateTensors used in pipeline parallelism
    from vllm.sequence import IntermediateTensors

    if isinstance(tensors, IntermediateTensors):
        ret = IntermediateTensors(
            {key: weak_ref_tensor(val) for key, val in tensors.tensors.items()}
        )
        return ret
    raise ValueError("Invalid type for tensors")