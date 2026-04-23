def __init__(
        self,
        gm: torch.fx.GraphModule,
        max_in_flight_gb: float,
        max_compute_pre_fetch: int,
        collective_bucketing: bool,
        insert_overlap_deps: bool,
        compute_overlap_multipler: float,
        max_coll_distance: int,
        custom_runtime_estimation: Callable[[fx.Node, int | None], float | None]
        | None = None,
        collective_estimator: Literal["analytical", "benchmark"] = "analytical",
        compute_estimator: Literal["analytical", "benchmark"] = "benchmark",
        max_memory_increase_gb: float | None = 1.0,
        max_memory_increase_ratio: float | None = 0.05,
        log_final_collectives_estimations: bool = False,
        bucket_exposed_first: bool | None = None,
        enable_fusion_regions: bool = False,
        bucket_only_internode_comms: bool = False,
        bucket_mode: BucketMode | None = None,
        max_off_bucket_gb: float | None = 0.5,
        prioritize_bucketing_during_scheduling: bool = True,
        pge_profile_path: str | None = None,
    ):
        self.gm = gm
        self.graph = gm.graph
        self.compute_overlap_multipler = compute_overlap_multipler
        self.max_node_distance = max_coll_distance
        self.max_in_flight_bytes: int = gb_to_bytes(max_in_flight_gb)

        # Profile-guided estimation: create estimator from profile path
        if pge_profile_path and custom_runtime_estimation is None:
            from torch._inductor.fx_passes.profile_guided_estimation import (
                ProfileGuidedEstimator,
            )

            custom_runtime_estimation = ProfileGuidedEstimator(
                pge_profile_path, diagnostics_gm=gm
            )

        self.custom_runtime_estimation = custom_runtime_estimation
        self.collective_bucketing = collective_bucketing
        self.insert_overlap_deps = insert_overlap_deps
        self.max_compute_pre_fetch = max_compute_pre_fetch
        # In deterministic mode, force analytical estimation to avoid GPU sync
        if config.deterministic:
            self.collective_estimator = "analytical"
            self.compute_estimator = "analytical"
        else:
            self.collective_estimator = collective_estimator
            self.compute_estimator = compute_estimator
        self.log_final_collectives_estimations = log_final_collectives_estimations
        self.bucket_exposed_first = bucket_exposed_first
        self.bucket_only_internode_comms = bucket_only_internode_comms
        self.bucket_mode = bucket_mode or _default_bucket_mode()
        self.max_off_bucket_bytes: int | None = (
            gb_to_bytes(max_off_bucket_gb) if max_off_bucket_gb is not None else None
        )
        self.prioritize_bucketing_during_scheduling = (
            prioritize_bucketing_during_scheduling
        )

        # Make all to(device) non_blocking=False,
        # They can be implicitly depending by user logic on other to(device) non_blocking=True.
        # OverlapScheduler can put reads of non_blocking device_put before blocking one.
        # This results in dirty reads.
        num_device_put_converted = make_all_device_put_sync(gm)
        if num_device_put_converted > 0:
            log.warning(
                "overlap_scheduling converted %d device_put operations from "
                "non_blocking=True to non_blocking=False. This may affect performance.",
                num_device_put_converted,
            )

        # Build fusion regions (mutates gm.graph) and compute initial node runtime
        # estimates. Compute nodes use roofline model here; the alignment step in
        # run() replaces them with benchmarked + cross-rank-aligned values.
        self.node_estimations, self.region_of = gather_node_runtime_estimations(
            gm,
            custom_runtime_estimation,
            enable_fusion_regions=enable_fusion_regions,
            log_estimations=True,
        )
        if self.region_of:
            # fuse_by_partitions replaces gm.graph, so we need to update our reference
            self.graph = gm.graph

        # Build structures
        stable_topological_sort(self.graph)
        self.nodes = list(self.graph.nodes)
        self.node_idx = {n: i for i, n in enumerate(self.nodes)}
        self.node_ancestors: dict[fx.Node, OrderedSet[fx.Node]] = (
            self._collect_node_ancestors()
        )

        # Identify collectives and compute nodes
        self.collective_info: dict[fx.Node, CollectiveInfo] = {}
        self.unscheduled_collectives: OrderedSet[fx.Node] = OrderedSet()

        # Identify compute nodes early (needed for baseline memory computation)
        self.compute_nodes = [n for n in self.nodes if is_compute_node(n)]
        self.current_compute_index = 0

        # Compute baseline memory profile from original schedule
        self.original_mem_before_compute_index: list[int] = []
        self.original_peak_memory = self._compute_baseline_memory()

        # Maximum allowed peak memory = baseline + max(absolute, ratio * baseline)
        # When both limits are specified, use the more permissive one
        memory_increase_bytes = None
        if max_memory_increase_gb is not None:
            memory_increase_bytes = gb_to_bytes(max_memory_increase_gb)
        if max_memory_increase_ratio is not None:
            ratio_increase = int(self.original_peak_memory * max_memory_increase_ratio)
            memory_increase_bytes = (
                max(memory_increase_bytes, ratio_increase)
                if memory_increase_bytes is not None
                else ratio_increase
            )
        if memory_increase_bytes is None:
            memory_increase_bytes = 0

        self.allowed_peak_memory_bytes = (
            self.original_peak_memory + memory_increase_bytes
        )

        # Track cumulative prefetch memory at each compute index
        # When we prefetch a collective at compute index i that will be used at index j,
        # it adds memory from i to j, so we need to track this cumulative effect
        self.cumulative_prefetch_mem_by_compute_index: list[int] = [
            0 for _ in range(len(self.compute_nodes))
        ]

        self.memory_tracker = MemoryTracker(self.graph)

        self.wait_to_start: dict[fx.Node, fx.Node] = {}
        self._identify_collectives()
        self.wasted_compute = 0.0

        # Calculate domination indices for both compute and reduce_scatter nodes
        self.reduce_scatter_nodes = self.graph.find_nodes(
            op="call_function",
            target=torch.ops._c10d_functional.reduce_scatter_tensor.default,
        )
        self.compute_index_domination = self._calculate_domination_index(
            self.compute_nodes
        )
        self.reduce_scatter_domination = self._calculate_domination_index(
            self.reduce_scatter_nodes
        )

        # Scheduling state
        self.potentially_hidden_collectives = (
            self.compute_potential_hidden_collectives()
        )
        self.potentially_hidden_waits = self.compute_potential_hidden_waits()
        self.in_degree = Counter(user for node in self.nodes for user in node.users)

        # Two separate queues: on-path (domination-based) and off-path (node_idx-based)
        self.on_path_ready: list[tuple[object, fx.Node]] = []
        self.off_path_ready: list[tuple[object, fx.Node]] = []
        # Track potential bucket sizes for off-path collectives (for batch scheduling)
        self.off_path_ready_potential_buckets: dict[object, int] = defaultdict(int)

        for node in self.nodes:
            if self.in_degree[node] == 0:
                self._add_to_ready_queue(node)

        self.in_flight: dict[fx.Node, CollectiveInfo] = {}  # start -> info
        self.in_flight_bytes = 0
        self.scheduled: OrderedSet[fx.Node] = OrderedSet()
        self.max_compute_pre_fetch = max_compute_pre_fetch

        self.last_on_path_node_idx = -1