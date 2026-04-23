def __init__(
        self,
        vllm_config: "VllmConfig",
        role: KVConnectorRole,
        parent: KVConnectorBase_V1,
    ):
        assert vllm_config.kv_transfer_config is not None
        self._parent = parent
        self._vllm_config = vllm_config
        self.kv_role = vllm_config.kv_transfer_config.kv_role
        self.worker_count = vllm_config.parallel_config.tensor_parallel_size
        config = lmcache_get_or_create_config()
        assert isinstance(config, LMCacheEngineConfig), (
            "LMCache v1 configuration is should be passed for vLLM v1."
        )
        # Put the leading with "lmcache." and matched configs from
        # vllm extra_config to the config
        kv_connector_extra_config = (
            vllm_config.kv_transfer_config.kv_connector_extra_config
        )
        if kv_connector_extra_config:
            for key, value in kv_connector_extra_config.items():
                if key.startswith("lmcache."):
                    config_key = key[8:]  # Remove "lmcache." prefix
                    if _validate_and_set_config_value(config, config_key, value):
                        logger.info(
                            "Updated config %s from vLLM extra config: %s",
                            config_key,
                            value,
                        )

        self.config = config

        self.async_loading = config.enable_async_loading
        self.layerwise_retrievers: list[Generator[torch.Tensor | None, None, None]] = []
        self._stats_monitor = LMCStatsMonitor.GetOrCreate()
        if role == KVConnectorRole.SCHEDULER:
            # Create lookup client using factory
            self.lookup_client = LookupClientFactory.create_lookup_client(
                vllm_config, config
            )
            self._unfinished_requests: dict[str, Request] = {}
            self._lookup_requests_in_step: list[str] = []
            self.lmcache_engine = None
        else:
            self.lmcache_engine = _init_lmcache_engine(
                config,
                vllm_config,
            )

            self.use_layerwise = config.use_layerwise
            self.enable_blending = config.enable_blending

            if self.enable_blending:
                self.blender = LMCBlenderBuilder.get_or_create(
                    ENGINE_NAME,
                    self.lmcache_engine,
                    self.lmcache_engine.gpu_connector,
                    config,
                )

            # Create lookup server using factory
            assert self.lmcache_engine is not None
            self.lookup_server = LookupClientFactory.create_lookup_server(
                self.lmcache_engine, vllm_config
            )

            self.offload_server = ZMQOffloadServer(
                self.lmcache_engine,
                vllm_config,
                get_tensor_model_parallel_rank(),
            )

            # In case of MLA, the lookup server is only created on worker 0
            if self.async_loading and self.lookup_server is not None:
                assert isinstance(self.lookup_server, LMCacheAsyncLookupServer)
                self.lmcache_engine.post_init(async_lookup_server=self.lookup_server)

        self.kv_caches: dict[str, torch.Tensor] = {}

        self._block_size = vllm_config.cache_config.block_size

        # request_id -> (vllm cached tokens, lmcache cached tokens)
        self.load_specs: dict[str, LoadSpec] = {}

        self.kv_cache_manager: KVCacheManager | None = None

        # request_id -> full_token_ids
        self._request_trackers: dict[str, RequestTracker] = {}

        # Whether to discard partial chunks
        self._discard_partial_chunks = (
            vllm_config.kv_transfer_config.get_from_extra_config(
                "discard_partial_chunks", False
            )
            or not config.save_unfull_chunk
        )

        self._lmcache_chunk_size = config.chunk_size
        self._save_decode_cache = config.save_decode_cache

        self.skip_last_n_tokens = vllm_config.kv_transfer_config.get_from_extra_config(
            "skip_last_n_tokens", 0
        )

        self.num_layers = vllm_config.model_config.get_num_layers(
            vllm_config.parallel_config
        )
        self.current_layer = 0

        self.force_skip_save = bool(os.environ.get("LMCACHE_FORCE_SKIP_SAVE", False))

        self._requests_priority: dict[str, int] = {}

        # TODO(baoloongmao): Internal api server & plugin framework support
        # dp > 1
        if (
            vllm_config.parallel_config.data_parallel_size_local == 1
            or vllm_config.parallel_config.data_parallel_rank_local == 0
        ):
            # Start internal API server if enabled
            # The enabled check is in the InternalAPIServer constructor
            self.api_server = InternalAPIServer(self)
            self.api_server.start()
            # Launch plugins
            self.plugin_launcher = RuntimePluginLauncher(
                self.config,
                role,
                self.worker_count,
                -1
                if self.lmcache_engine is None  # scheduler side
                else self.lmcache_engine.metadata.worker_id,
            )
            self.plugin_launcher.launch_plugins()
        else:
            self.api_server = None  # type: ignore[assignment]
            self.plugin_launcher = None  # type: ignore[assignment]
        logger.info(
            "LMCache initialized for role %s with version %s, "
            "vllm version %s, lmcache cache_engine metadata: %s",
            role,
            utils.get_version(),
            VLLM_VERSION,
            getattr(self.lmcache_engine, "metadata", None),
        )