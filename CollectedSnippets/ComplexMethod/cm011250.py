def _parse_and_validate_remote_device(pg, remote_device):
    if remote_device is None:
        raise ValueError("remote device is None")

    worker_name = remote_device.worker_name()
    rank = remote_device.rank()
    device = remote_device.device()

    # Validate rank, skip validation if rank is not part of process group.
    if rank is not None and not c10d._rank_not_in_group(pg):
        pg_global_ranks = c10d.get_process_group_ranks(pg)
        if rank not in pg_global_ranks:
            raise ValueError(
                f"Global rank {rank} does not exist in input process group: {pg_global_ranks}"
            )

    if worker_name is not None:
        if not rpc._is_current_rpc_agent_set():
            raise RuntimeError(
                f"RPC framework needs to be initialized for using worker names: {worker_name}"
            )

        workers = rpc._get_current_rpc_agent().get_worker_infos()
        for worker in workers:
            if worker.name == worker_name:
                return worker.id, device

        raise ValueError(f"Invalid worker name: {worker_name}")

    return rank, device