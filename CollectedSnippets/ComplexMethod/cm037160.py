def initialize_ray_cluster(
    parallel_config: ParallelConfig,
    ray_address: str | None = None,
    require_gpu_on_driver: bool = True,
):
    """Initialize the distributed cluster with Ray.

    it will connect to the Ray cluster and create a placement group
    for the workers, which includes the specification of the resources
    for each distributed worker.

    Args:
        parallel_config: The configurations for parallel execution.
        ray_address: The address of the Ray cluster. If None, uses
            the default Ray cluster address.
        require_gpu_on_driver: If True (default), require at least one GPU
            on the current (driver) node and pin the first PG bundle to it.
            Set to False for executors like RayExecutorV2 where all GPU work
            is delegated to remote Ray actors.
    """
    assert_ray_available()
    from vllm.platforms import current_platform

    # Disable Ray usage stats collection
    if os.environ.get("RAY_USAGE_STATS_ENABLED", "0") != "1":
        os.environ["RAY_USAGE_STATS_ENABLED"] = "0"

    # Prevalidate GPU requirements before Ray processing
    if current_platform.is_cuda() and parallel_config.world_size > 1:
        available_gpus = current_platform.device_count()
        if parallel_config.world_size > available_gpus:
            logger.warning(
                "Tensor parallel size (%d) exceeds available GPUs (%d). "
                "This may result in Ray placement group allocation failures. "
                "Consider reducing tensor_parallel_size to %d or less, "
                "or ensure your Ray cluster has %d GPUs available.",
                parallel_config.world_size,
                available_gpus,
                available_gpus,
                parallel_config.world_size,
            )

    if ray.is_initialized():
        logger.info("Ray is already initialized. Skipping Ray initialization.")
    elif current_platform.is_rocm() or current_platform.is_xpu():
        # Try to connect existing ray instance and create a new one if not found
        try:
            ray.init("auto")
        except ConnectionError:
            logger.warning(
                "No existing RAY instance detected. "
                "A new instance will be launched with current node resources."
            )
            ray.init(
                address=ray_address,
                num_gpus=parallel_config.world_size,
                runtime_env=parallel_config.ray_runtime_env,
            )
    else:
        ray.init(address=ray_address, runtime_env=parallel_config.ray_runtime_env)

    device_str = current_platform.ray_device_key
    if not device_str:
        raise ValueError(
            f"current platform {current_platform.device_name} does not support ray."
        )

    # Create or get the placement group for worker processes
    if parallel_config.placement_group:
        current_placement_group = parallel_config.placement_group
    else:
        current_placement_group = ray.util.get_current_placement_group()

    if current_placement_group:
        logger.info("Using the existing placement group")

        # We are in a placement group
        bundles = current_placement_group.bundle_specs
        # Verify that we can use the placement group.
        device_bundles = 0
        for bundle in bundles:
            bundle_devices = bundle.get(device_str, 0)
            if bundle_devices > 1:
                raise ValueError(
                    f"Placement group bundle cannot have more than 1 {device_str}."
                )
            if bundle_devices:
                device_bundles += 1
        if parallel_config.world_size > device_bundles:
            raise ValueError(
                f"The number of required {device_str}s exceeds the total "
                f"number of available {device_str}s in the placement group. "
                f"Required number of devices: {parallel_config.world_size}. "
                f"Total number of devices: {device_bundles}."
            )
    else:
        logger.info("No current placement group found. Creating a new placement group.")
        num_devices_in_cluster = ray.cluster_resources().get(device_str, 0)
        # Log a warning message and delay resource allocation failure response.
        # Avoid immediate rejection to allow user-initiated placement group
        # created and wait cluster to be ready
        if parallel_config.world_size > num_devices_in_cluster:
            logger.warning(
                "The number of required %ss exceeds the total "
                "number of available %ss in the placement group.",
                device_str,
                device_str,
            )
        # Create a new placement group
        placement_group_specs: list[dict[str, float]] = [
            {device_str: 1.0} for _ in range(parallel_config.world_size)
        ]

        # vLLM engine is also a worker to execute model with an accelerator,
        # so it requires to have the device in a current node. Check if
        # the current node has at least one device.
        current_ip = get_ip()
        current_node_id = ray.get_runtime_context().get_node_id()
        current_node_resource = available_resources_per_node()[current_node_id]
        # TODO (jeffreywang): require_gpu_on_driver should be always False
        # after deprecating RayDistributedExecutor.
        if require_gpu_on_driver:
            if current_node_resource.get(device_str, 0) < 1:
                raise ValueError(
                    f"Current node has no {device_str} available. "
                    f"{current_node_resource=}. vLLM engine cannot start "
                    f"without {device_str}. Make sure you have at least 1 "
                    f"{device_str} available in a node "
                    f"{current_node_id=} {current_ip=}."
                )
            # This way, at least bundle is required to be created in a
            # current node.
            placement_group_specs[0][f"node:{current_ip}"] = 0.001

        # By default, Ray packs resources as much as possible.
        current_placement_group = ray.util.placement_group(
            placement_group_specs, strategy="PACK"
        )
        _wait_until_pg_ready(current_placement_group)

    assert current_placement_group is not None
    _verify_bundles(
        current_placement_group, parallel_config, device_str, require_gpu_on_driver
    )
    # Set the placement group in the parallel config
    parallel_config.placement_group = current_placement_group