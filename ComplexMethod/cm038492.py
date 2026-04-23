def __init__(self, vllm_config: VllmConfig, engine_id: str):
        if not is_moriio_available():
            raise RuntimeError(
                "MoRIIO is not available. Please ensure the 'mori' package "
                "is installed and properly configured."
            )

        self.moriio_config = MoRIIOConfig.from_vllm_config(vllm_config)
        self.mode = get_moriio_mode()

        logger.info("Initializing MoRIIO worker %s", engine_id)

        logging.getLogger("aiter").disabled = True

        # Config.
        self.vllm_config = vllm_config
        assert vllm_config.kv_transfer_config is not None, (
            "kv_transfer_config must be set for MoRIIOConnector"
        )
        self.kv_transfer_config = vllm_config.kv_transfer_config
        self.is_producer = self.kv_transfer_config.is_kv_producer

        if self.is_producer:
            set_role(ROLE.PRODUCER)
        else:
            set_role(ROLE.CONSUMER)
        # mori engine
        self._rank = get_world_group().rank
        self._local_rank = get_world_group().local_rank
        self.tp_rank = self.moriio_config.tp_rank
        self.dp_rank = self.moriio_config.dp_rank

        self.local_ip = self.moriio_config.local_ip
        self.local_kv_port = self.moriio_config.local_kv_port
        self.proxy_ip = self.moriio_config.proxy_ip
        self.local_ping_port = self.moriio_config.local_ping_port
        self.proxy_ping_port = self.moriio_config.proxy_ping_port
        self.http_port = self.moriio_config.http_port
        self.handshake_port = self.moriio_config.handshake_port
        self.notify_port = self.moriio_config.notify_port

        self.zmq_context = zmq.Context()
        self.metadata_address = (
            f"{self.moriio_config.local_ip}:{self.moriio_config.local_ping_port}"
        )
        self.request_address = (
            f"{self.moriio_config.local_ip}:{self.moriio_config.http_port}"
        )

        self.moriio_engine = None
        self._handle_request_thread = None
        self._ping_thread = None
        self._writer = MoRIIOWriter(self)

        role = "producer" if self.is_producer else "consumer"
        engine_suffix = (
            f"{self.moriio_config.local_ip}:{self.moriio_config.handshake_port}:"
            f"tp{self.tp_rank}:dp{self.dp_rank}"
        )
        self.moriio_engine = IOEngine(
            f"{role}:{engine_suffix}",
            IOEngineConfig(
                self.moriio_config.local_ip, self.moriio_config.local_kv_port
            ),
        )
        logger.debug(
            "build MORI IOEngine %s (ip=%s port=%s)",
            f"{role}:{engine_suffix}",
            self.moriio_config.local_ip,
            self.moriio_config.local_kv_port,
        )

        if self._rank == 0 and self.moriio_config.proxy_ip:
            self._ping_thread = threading.Thread(
                target=self._ping, args=(self.zmq_context,), daemon=True
            )
            self._ping_thread.start()

        logger.info(
            "Initializing MoRIIO Engine, engine = %s, role = %s",
            self.moriio_engine,
            "producer" if self.is_producer else "consumer",
        )

        # Agent.
        self.moriio_wrapper = MoRIIOWrapper(tp_rank=self.tp_rank, dp_rank=self.dp_rank)
        self.moriio_wrapper.set_moriio_engine(self.moriio_engine)
        self.moriio_wrapper.set_backend_type(BackendType.RDMA)
        self.moriio_wrapper.notify_port = self.moriio_config.notify_port
        self.local_kv_cache_metadata: list[bytes] = []
        self.local_kv_cache_size: list[int] = []
        self.layer_name_to_local_kv_cache_metadata: dict[str, list[bytes]] = {}

        self.remote_kv_cache_metadata: list[bytes] = []
        self.remote_kv_cache_size: list[int] = []
        self.layer_name_to_remote_kv_cache_metadata: dict[str, dict[str, list[Any]]] = (
            dict()
        )
        self.remote_moriio_metadata: dict[EngineId, MoRIIOAgentMetadata] = {}
        self.slot_size_bytes = 0

        self.load_ready_flag: dict[str, bool] = {}
        self.write_ready_flags: dict[str, bool] = {}
        self.kv_cache_shape = None
        self.block_shape = None
        self.kv_element_size = 0

        # Map of engine_id -> {agent_name0, agent_name1..}.
        self._remote_agents: dict[EngineId, set[str]] = {}

        self.side_channel_port: int = (
            self.moriio_config.handshake_port
            + get_port_offset(self.dp_rank, self.tp_rank)
        )
        self.engine_id: EngineId = engine_id

        self.world_size = get_tensor_model_parallel_world_size()
        self.tp_group = get_tp_group()

        # KV Caches and moriio tracking data.
        self.kv_caches: dict[str, torch.Tensor] = {}

        # Map of engine_id -> kv_caches_base_addr. For TP case, each local
        # rank will still only pull from a single remote TP worker.
        self.kv_caches_base_addr: dict[EngineId, list[int]] = {}

        # Number of MoRIIO regions. Currently one region per cache
        # (so 1 per layer for MLA, otherwise 2 per layer)
        self.num_regions = 0
        self.num_layers = 0

        # Map of engine_id -> num_blocks. All ranks in the same deployment will
        # have the same number of blocks.
        self.dst_num_blocks: dict[EngineId, int] = {}
        # In progress transfers.
        self._recving_transfers: defaultdict[ReqId, list] = defaultdict(list)
        self._recving_transfers_callback_addr: dict[ReqId, tuple[str, str]] = {}

        # Track the expiration time of requests that are waiting to be sent.
        self._reqs_to_send: dict[ReqId, float] = {}

        # Background thread for handling new handshake requests.
        self._moriio_handshake_listener_t: threading.Thread | None = None
        # Background thread for initializing new MoRIIO handshakes.
        self._handshake_initiation_executor = ThreadPoolExecutor(
            # MoRIIO is not guaranteed to be thread-safe, limit 1 worker.
            max_workers=1,
            thread_name_prefix="vllm-moriio-handshake-initiator",
        )
        self._ready_requests = queue.Queue[tuple[ReqId, ReqMeta]]()
        self._handshake_futures: dict[EngineId, Future[set[str]]] = {}
        # Protects _handshake_futures and _remote_agents.
        self._handshake_lock = threading.RLock()

        self.block_size = vllm_config.cache_config.block_size
        self.model_config = vllm_config.model_config
        self.cache_config = vllm_config.cache_config

        self.block_window_per_layer: list[int | None] = []
        self.use_mla = self.model_config.use_mla
        self.built_session = False
        self.built_write_session: defaultdict[str, list] = defaultdict(list)
        backend = get_attn_backend(
            self.model_config.get_head_size(),
            self.model_config.dtype,
            self.cache_config.cache_dtype,
            use_mla=self.use_mla,
        )
        self.transfer_id_to_request_id: dict[TransferId, ReqId] = {}

        # TODO: consider the integration of flashinfer or other backends.
        self.backend_name = backend.get_name()
        logger.debug("Detected attention backend %s", self.backend_name)