def __init__(
        self,
        vllm_config: VllmConfig,
        addresses: EngineZmqAddresses,
        executor_class: type[Executor],
        log_stats: bool,
        placement_groups: list["PlacementGroup"] | None = None,
        local_dp_ranks: list[int] | None = None,
    ):
        import copy

        import ray
        from ray.runtime_env import RuntimeEnv
        from ray.util.scheduling_strategies import PlacementGroupSchedulingStrategy

        from vllm.v1.engine.core import DPMoEEngineCoreActor, EngineCoreActor

        dp_size = vllm_config.parallel_config.data_parallel_size
        actor_class = (
            DPMoEEngineCoreActor
            if dp_size > 1 and vllm_config.model_config.is_moe
            else EngineCoreActor
        )

        self.local_engine_actors: list[ray.ActorHandle] = []
        self.remote_engine_actors: list[ray.ActorHandle] = []

        env_vars_list = get_env_vars_to_copy(destination=actor_class.__name__)
        self.env_vars_dict = {
            name: os.environ[name] for name in env_vars_list if name in os.environ
        }
        runtime_env = RuntimeEnv(env_vars=self.env_vars_dict)

        self.addresses = addresses
        self.executor_class = executor_class
        self.log_stats = log_stats
        local_engine_count = vllm_config.parallel_config.data_parallel_size_local
        world_size = vllm_config.parallel_config.world_size
        self.manager_stopped = threading.Event()
        self.failed_proc_name: str | None = None

        if ray.is_initialized():
            logger.info("Ray is already initialized. Skipping Ray initialization.")
        else:
            ray.init()

        parallel_config = vllm_config.parallel_config
        if parallel_config.enable_elastic_ep:
            from vllm.distributed.utils import create_tcp_store

            ip = parallel_config.data_parallel_master_ip
            store = create_tcp_store(
                ip,
                0,
                is_master=True,
                world_size=-1,
                wait_for_workers=False,
            )
            parallel_config._coord_store_port = store.port
            self._coord_store = store

        if placement_groups is not None:
            assert local_dp_ranks is not None, (
                "local_dp_ranks must be provided if placement_groups is provided"
            )
            assert len(placement_groups) == len(local_dp_ranks), (
                "placement_groups and local_dp_ranks must have the same length"
            )
            logger.info("Using provided placement groups")
            # TODO(rui): validate passed-in placement groups
            self.created_placement_groups = []
        else:
            placement_groups, local_dp_ranks = (
                CoreEngineActorManager.create_dp_placement_groups(vllm_config)
            )
            self.created_placement_groups = placement_groups
        assert len(placement_groups) == dp_size, (
            "Number of placement groups must match data parallel size"
        )

        self.placement_group_is_local = []
        refs = []
        for index, local_index, pg in zip(
            range(dp_size), local_dp_ranks, placement_groups
        ):
            dp_vllm_config = copy.deepcopy(vllm_config)
            dp_vllm_config.parallel_config.placement_group = pg
            local_client = index < local_engine_count

            if dp_size > 1 and dp_vllm_config.kv_transfer_config is not None:
                # modify the engine_id and append the local_dp_rank to it to ensure
                # that the kv_transfer_config is unique for each DP rank.
                dp_vllm_config.kv_transfer_config.engine_id = (
                    f"{dp_vllm_config.kv_transfer_config.engine_id}_dp{local_index}"
                )

            # Ray XPU known issue: dpctl initializes the GPU runtime early, so
            # setting device env vars in Ray actor's initialization method
            # will not affect device selection. See:
            # https://github.com/ray-project/ray/blob/master/python/ray/_private/accelerators/intel_gpu.py#L56 # noqa: E501
            if current_platform.is_xpu():
                device_evar = current_platform.device_control_env_var
                device_indices = get_device_indices(
                    device_evar, local_index, world_size
                )
                actor_env_vars = self.env_vars_dict.copy()
                actor_env_vars[device_evar] = device_indices
                runtime_env = RuntimeEnv(env_vars=actor_env_vars)

            actor = (
                ray.remote(actor_class)
                .options(
                    scheduling_strategy=PlacementGroupSchedulingStrategy(
                        placement_group=pg,
                        placement_group_bundle_index=world_size,
                    ),
                    runtime_env=runtime_env,
                )
                .remote(
                    vllm_config=dp_vllm_config,
                    executor_class=executor_class,
                    log_stats=log_stats,
                    local_client=local_client,
                    addresses=addresses,
                    dp_rank=index,
                    local_dp_rank=local_index,
                )
            )
            if local_client:
                self.local_engine_actors.append(actor)
            else:
                self.remote_engine_actors.append(actor)
            self.placement_group_is_local.append(local_client)
            refs.append(actor.wait_for_init.remote())

        ray.get(refs)
        self.run_refs = []
        self.actor_run_ref_dict = dict()
        for actor in self.local_engine_actors + self.remote_engine_actors:
            ref = actor.run.remote()
            self.run_refs.append(ref)
            self.actor_run_ref_dict[actor] = ref