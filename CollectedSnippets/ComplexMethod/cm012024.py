def estimate_nccl_collective_runtime_impl(
    tensor_storage_size_bytes: int, group_size: int, coll: NCCL_COLL
) -> float:
    """
    Returns estimated NCCL collective runtime in milliseconds (ms).

    The following heuristics are copied from https://github.com/NVIDIA/nccl/blob/master/src/graph/tuning.cc.
    We aim to estimate the runtime as accurately as possible.

    Assumptions:
    - only ring algorithm (NCCL_ALGO_RING) is used
    - only Low-Latency protocol (NCCL_PROTO_LL) is used, i.e. Simple or LL128 is not used
    - 8 gpus per node  # TODO: Need to find a way to get accurate "gpus per node" and "# nodes" info.
    - collective is one of: allreduce, reducescatter, allgather
    """
    # Convert bytes to GB
    tensor_storage_size_GB = tensor_storage_size_bytes / 1024 / 1024 / 1024

    # Currently assumes each node has 8 gpus. And when >1 node is used, assumes each node uses all 8 gpus.
    # TODO: Need to find a way to get accurate "gpus per node" and "# nodes" info.
    num_gpus_per_node = 8
    nNodes = math.ceil(group_size / num_gpus_per_node)
    nRanks = group_size  # this is total # of gpus globally that participate in this collective op

    if nRanks <= 1:
        return 0

    if coll == NCCL_COLL.UNSUPPORTED:
        return 0

    # Assumes ring algorithm
    nccl_algo = NCCL_ALGO.RING
    nccl_proto = NCCL_PROTO.LL

    # =============== bandwidth computation ===============
    # First compute bandwidth in GB/s; then at the end, convert it to GB/ns

    bwIntra = torch._inductor.config.intra_node_bw
    bwInter = torch._inductor.config.inter_node_bw

    compCapIndex = get_gpu_type()
    index2 = nNodes - 1 if nNodes <= 2 else 2
    # LL: for single node, we look at GPU type; for multi-node, we look at CPU type
    index1 = compCapIndex if nNodes == 1 else 0
    llMaxBw = llMaxBws[index1][index2]

    # NOTE: each step of ring algorithm is synchronized,
    # and is bottlenecked by the slowest link which is the inter-node interconnect.
    # hence when nNodes >= 2, bw is inter-node bandwidth.
    # NOTE: the original code in https://github.com/NVIDIA/nccl/blob/master/src/graph/tuning.cc
    # have this as `if nNodes <= 2` which seems wrong. Corrected it here.
    bw = bwIntra if nNodes == 1 else bwInter
    nChannels = 2  # Assume # channels is 2
    busBw = nChannels * bw

    # Various model refinements
    busBw = min(
        llMaxBw,
        busBw
        * (1.0 / 4.0 if (nNodes > 1 or coll == NCCL_COLL.ALL_REDUCE) else 1.0 / 3.0),
    )

    if coll == NCCL_COLL.ALL_REDUCE:
        nsteps = 2 * (nRanks - 1)
    elif coll == NCCL_COLL.ALL_TO_ALL:
        nsteps = 2 * (nRanks - 1)
    elif coll in (NCCL_COLL.REDUCE_SCATTER, NCCL_COLL.ALL_GATHER):
        nsteps = nRanks - 1
    elif coll == NCCL_COLL.P2P:
        # assume 1 hop per pair
        nsteps = 1

    # Convert bus BW to algorithm BW (tensor bytes / algoBW = actual execution time)
    ratio = (1.0 * nRanks) / nsteps  # type: ignore[possibly-undefined]
    bandwidth = busBw * ratio
    # Convert GB/s to GB/ns
    bandwidth_GB_per_ns = bandwidth / 1e9

    # =============== latency computation ===============
    intraHw = NCCL_HW.NVLINK

    if coll == NCCL_COLL.ALL_REDUCE:
        if nNodes > 1:
            nInterSteps = 2 * nNodes
        else:
            nInterSteps = 0
    elif coll in (NCCL_COLL.REDUCE_SCATTER, NCCL_COLL.ALL_GATHER, NCCL_COLL.ALL_TO_ALL):
        nInterSteps = nNodes - 1
    elif coll == NCCL_COLL.P2P:
        # p2p may cross node bdry
        nInterSteps = 1 if nNodes > 1 else 0

    # First compute latency in us; then at the end, convert it to ns
    latency = baseLat[nccl_algo][nccl_proto]
    intraLat = hwLat[intraHw][nccl_algo][nccl_proto]
    interLat = hwLat[NCCL_HW.NET][nccl_algo][nccl_proto]

    # Inter-node rings still have to launch nsteps * net overhead.
    netOverhead = 0.0
    if nNodes > 1:
        netOverhead = 1.0  # getNetOverhead(comm);
    intraLat = max(intraLat, netOverhead)
    latency += (nsteps - nInterSteps) * intraLat + nInterSteps * interLat  # type: ignore[possibly-undefined]
    # Convert us to ns
    latency_ns = latency * 1e3

    # =============== final result ===============
    transport_ns = tensor_storage_size_GB / bandwidth_GB_per_ns
    ns = transport_ns + latency_ns
    ms = ns / 1e6
    return ms