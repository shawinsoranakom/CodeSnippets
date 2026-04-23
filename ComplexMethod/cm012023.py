def get_collective_type_from_kernel_name(kernel_name: str) -> NCCL_COLL:
    assert kernel_name is not None
    if "all_reduce" in kernel_name:
        return NCCL_COLL.ALL_REDUCE
    elif "all_gather" in kernel_name:
        return NCCL_COLL.ALL_GATHER
    elif "reduce_scatter" in kernel_name:
        return NCCL_COLL.REDUCE_SCATTER
    elif any(comm in kernel_name for comm in ("all_to_all", "alltoall")):
        return NCCL_COLL.ALL_TO_ALL
    elif any(comm in kernel_name for comm in ("isend", "irecv", "batch_p2p")):
        return NCCL_COLL.P2P
    else:
        return NCCL_COLL.UNSUPPORTED