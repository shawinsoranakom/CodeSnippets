def get_tensor_shard(param, empty_param, device_mesh, rank, dim, tensor_idx: int | None = None):
    """
    Generalized tensor sharding across a multi-dimensional device mesh.
    Extract only the fraction of the parameter owned by the given `rank` when the parameter would have gone sharding at provided `dim`.
    Extraction follows the pytorch `Shard` placement so that sharding and materializing back to full tensor follows `Shard` semantics.
    `Shard` follows torch.chunk style sharding of the tensor. We demonstrate some cases below on how sharding happens including some edge cases
    such as some ranks having an empty tensor as shard. Below implementation is robut to all these cases.

    Case (1)
    empty_param                 (16, 5120, 8190)
    dim                         0
    device_mesh.size()          4
    rank 0 gets					(4, 5120, 8190)			 (0 ... 4, 5120, 8190)
    rank 1 gets					(4, 5120, 8190)			 (4 ... 8, 5120, 8190)
    rank 2 gets					(4, 5120, 8190)			 (8 ... 12, 5120, 8190)
    rank 3 gets					(4, 5120, 8190)			 (12 ... 16, 5120, 8190)

    Case (2)
    empty_param                 (16, 5120, 8190)
    dim                         0
    device_mesh.size()          14
    rank 0 gets					(2, 5120, 8190)			 (0 ... 2, 5120, 8190)
    rank 1 gets					(2, 5120, 8190)			 (2 ... 4, 5120, 8190)
    rank 2 gets					(2, 5120, 8190)			 (4 ... 6, 5120, 8190)
    rank 3 gets					(2, 5120, 8190)			 (6 ... 8, 5120, 8190)
    rank 4 gets					(2, 5120, 8190)			 (8 ... 10, 5120, 8190)
    rank 5 gets					(2, 5120, 8190)			 (10 ... 12, 5120, 8190)
    rank 6 gets					(2, 5120, 8190)			 (12 ... 14, 5120, 8190)
    rank 7 gets					(2, 5120, 8190)			 (14 ... 16, 5120, 8190)
    rank 8 gets					(0, 5120, 8190)
    rank 9 gets					(0, 5120, 8190)
    rank 10 gets			    (0, 5120, 8190)
    rank 11 gets				(0, 5120, 8190)
    rank 12 gets				(0, 5120, 8190)
    rank 13 gets				(0, 5120, 8190)

    Case (3)
    empty_param                 (16, 5120, 8190)
    dim                         0
    device_mesh.size()          3
    rank 0 gets					(6, 5120, 8190)			 (0 ... 6, 5120, 8190)
    rank 1 gets					(6, 5120, 8190)			 (6 ... 12, 5120, 8190)
    rank 2 gets					(4, 5120, 8190)			 (12 ... 16, 5120, 8190)

    In case (2), empty shards are returned with appropriate dimension to allow for operations to work smoothly.
    Args:
        param (torch.Tensor): The tensor to shard.
        empty_param (torch.Tensor): A tensor used for shape reference.
        device_mesh (torch.Tensor): Shape [d_0, ..., d_n] representing the mesh.
        rank (int): Global rank of the current process/device.
        dim (int): Dimension along which to shard the tensor.
    """
    param_dim = empty_param.ndim
    mesh_shape = device_mesh.shape
    world_size = reduce(operator.mul, mesh_shape)
    # Get param shape: works for both torch.Tensor and safetensors TensorInfo
    param_shape = list(param.shape) if isinstance(param, torch.Tensor) else param.get_shape()
    if dim < 0:
        dim = param_dim + dim
    if empty_param.dim() == 3 and dim == 1 and len(param_shape) == 2:
        dim = 0
    elif empty_param.dim() == 3 and dim == 2 and len(param_shape) == 2:
        dim = 1

    shard_size = math.ceil(param_shape[dim] / world_size)
    start = rank * shard_size
    end = min(start + shard_size, param_shape[dim])

    if dim >= param_dim:
        raise ValueError(f"dim {dim} is out of bounds for tensor of dimension {param_dim}")

    if rank >= world_size:
        raise ValueError(f"Rank {rank} is out of bounds for mesh size {world_size}")

    # we have the full tensor not 1 part of it.
    # in that case, we just assume that the weight was properly saved
    # and thus because we TP if the layer is colwise it should not use this. Layer should be packed_colwise
    # to inform that it needs to read form a packed tensor. It will also take care of the module list thingy.
    # here we take care of potential chunking / layer split / layer chunking.
    # The only "hard" case is? if we collect q,k,v -> merge it into qkv. In that case
    # actually we still shard dim=0 does not change
    # so only case is if the dim of the empty param is 3 and the shard dim is 0 -> we put the
    # tensor on a certain device (with the input tensor_index)
    if tensor_idx is not None and empty_param.dim() == 3 and dim == 0 and len(param_shape) == 2:
        # special case we don't "shard" just send this entire tensor to the correct rank.
        if start <= tensor_idx < end:
            # this tensor does need to be materialized on this device:
            return param[:]
        else:
            return torch.empty([], dtype=torch.int64, device=rank)

    slice_indices = [slice(None)] * len(param_shape)

    if start < param_shape[dim]:
        slice_indices[dim] = slice(start, end)
        param = param[tuple(slice_indices)]
        if isinstance(param, list):  # TODO handle the modulelist case!
            param = [p[:] for p in param]
        return param

    param_shape[dim] = 0
    return torch.empty(tuple(param_shape), dtype=torch.int64)