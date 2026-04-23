def _is_nested_tensor(val: torch.Tensor) -> bool:
    if type(val) is ShardedTensor:
        if len(val.local_shards()) == 0:
            return False
        if type(val.local_shards()[0].tensor) is ShardedTensor:
            return True
        if type(val.local_shards()[0].tensor) is DTensor:
            raise ValueError("Cannot handle DTensor nested inside ShardedTensor")
    elif type(val) is DTensor and (
        type(val._local_tensor) is DTensor or type(val._local_tensor) is ShardedTensor
    ):
        raise ValueError("Cannot handle nested DTensor")
    return False