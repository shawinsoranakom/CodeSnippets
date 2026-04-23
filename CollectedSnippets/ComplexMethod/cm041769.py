def _ray_training_function(ray_args: "RayArguments", config: dict[str, Any]) -> None:
    num_workers = ray_args.ray_num_workers
    master_addr = ray_args.master_addr
    master_port = ray_args.master_port
    logger.info(f"Using ray.remote mode with {num_workers} workers for distributed training.")

    # initialize ray
    if not ray.is_initialized():
        if ray_args.ray_init_kwargs is not None:
            ray.init(**ray_args.ray_init_kwargs)
        else:
            ray.init()

    # verify resources
    device_name = get_device_name().upper()
    total_devices = int(ray.cluster_resources().get(device_name, 0))
    if num_workers > total_devices:
        raise ValueError(
            f"The number of devices in the Ray cluster ({total_devices}) should be greater than num_workers ({num_workers})."
        )

    # verify master_addr
    if master_addr is None:
        master_addr = get_ray_head_node_ip()
        logger.info(f"`master_addr` is not specified, using head node ip: {master_addr}.")
    else:
        nodes = [node["NodeManagerAddress"] for node in ray.nodes() if node["Alive"]]
        if master_addr not in nodes:
            raise ValueError(f"The `master_addr` ({master_addr}) is not in Ray cluster or not alive ")

    # create placementgroup for resource management
    pg, bundle = get_placement_group(total_devices)
    ray.get(pg.ready())
    logger.info(f"Create placement group with {num_workers} bundles: {bundle}")

    # get sorted_bundle_indices
    sorted_bundle_indices = sort_placement_group_by_node_ip(pg, master_addr)

    # get master port
    if master_port is None:
        master_port = find_available_port()
        logger.info(f"`master_port` is not specified, using available port: {master_port}.")
    master_port = str(master_port)

    # backing up environment variables
    current_env = dict(os.environ.items())

    # launch workers
    RayWorker = ray.remote(Worker)
    workers = []
    for rank in range(num_workers):
        remote_config = get_ray_remote_config_for_worker(
            placement_group=pg,
            bundle_idx=sorted_bundle_indices[rank],
            rank=rank,
            world_size=num_workers,
            master_addr=master_addr,
            master_port=master_port,
            env=current_env,
        )
        worker = RayWorker.options(**remote_config).remote()
        workers.append(worker)

    ray.get([worker._training_function.remote(config=config) for worker in workers])
    ray.shutdown()