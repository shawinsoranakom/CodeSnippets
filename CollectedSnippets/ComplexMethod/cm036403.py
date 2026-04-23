def __init__(
        self,
        offloaded_block_size: int,
        gpu_block_size: int,
        num_gpu_blocks: int,
        async_scheduling: bool = True,
    ):
        self.offloaded_block_size: int = offloaded_block_size
        self.gpu_block_size: int = gpu_block_size
        self.num_gpu_blocks: int = num_gpu_blocks
        self.async_scheduling: bool = async_scheduling

        self.req_id: int = -1

        vllm_config = create_vllm_config(
            block_size=gpu_block_size, max_num_batched_tokens=1000
        )
        vllm_config.scheduler_config.async_scheduling = async_scheduling
        vllm_config.kv_transfer_config = KVTransferConfig(
            kv_connector="OffloadingConnector",
            kv_role="kv_both",
            kv_connector_extra_config={
                "spec_name": "MockOffloadingSpec",
                "spec_module_path": "tests.v1.kv_connector.unit.offloading_connector.utils",  # noqa: E501
                "block_size": offloaded_block_size,
            },
        )

        block_size = vllm_config.cache_config.block_size
        kv_cache_config = KVCacheConfig(
            num_blocks=num_gpu_blocks,
            kv_cache_tensors=[],
            kv_cache_groups=[
                KVCacheGroupSpec(
                    ["layer"],
                    FullAttentionSpec(
                        block_size=block_size,
                        num_kv_heads=1,
                        head_size=1,
                        dtype=torch.float32,
                    ),
                )
            ],
        )
        vllm_config.cache_config.num_gpu_blocks = num_gpu_blocks
        self.num_kv_groups = len(kv_cache_config.kv_cache_groups)

        scheduler_cls = AsyncScheduler if async_scheduling else Scheduler
        self.scheduler = scheduler_cls(
            vllm_config=vllm_config,
            kv_cache_config=kv_cache_config,
            log_stats=True,
            structured_output_manager=StructuredOutputManager(vllm_config),
            block_size=block_size,
        )

        self.worker_connector = OffloadingConnector(
            vllm_config, KVConnectorRole.WORKER, kv_cache_config
        )

        # register worker kv_caches to enable OffloadingWorker creations
        # set_current_vllm_config is needed for get_kv_cache_layout() to work
        with set_current_vllm_config(vllm_config):
            self.worker_connector.register_cross_layers_kv_cache(
                kv_cache=torch.empty(0),
                attn_backend=FlashAttentionBackend,
            )

        # extract connector of scheduler
        scheduler_connector = self.scheduler.connector
        assert scheduler_connector is not None
        assert isinstance(scheduler_connector, OffloadingConnector)
        self.scheduler_connector: OffloadingConnector = scheduler_connector

        # extract mocked OffloadingManager of scheduler connector
        self.connector_scheduler = scheduler_connector.connector_scheduler
        assert self.connector_scheduler is not None
        manager = self.connector_scheduler.manager
        assert isinstance(manager, MagicMock)
        self.manager: MagicMock = manager

        assert len(self.connector_scheduler.config.kv_group_configs) == 1
        kv_group_config = self.connector_scheduler.config.kv_group_configs[0]
        assert kv_group_config.gpu_block_size == gpu_block_size
        assert kv_group_config.offloaded_block_size == offloaded_block_size

        # extract OffloadingSpec of worker_connector
        connector_worker = self.worker_connector.connector_worker
        assert connector_worker is not None
        offloading_spec = connector_worker.spec
        assert isinstance(offloading_spec, MockOffloadingSpec)
        self.offloading_spec: MockOffloadingSpec = offloading_spec

        # mapping (offloading address) -> gpu_block_index
        self.offloaded: dict[Any, int] = {}

        self.completed_loads: list[TransferSummary] = []
        self.completed_stores: list[TransferSummary] = []
        self.flushed_gpu_block_indexes: set[int] = set()

        # maps {block_id: block_offset}
        self.gpu_block_index: dict[int, int] = {}

        init_none_hash(sha256)
        self._block_hasher = get_request_block_hasher(gpu_block_size, sha256)

        self._dummy_ctx: ForwardContext = ForwardContext(
            no_compile_layers={},
            attn_metadata={},
            slot_mapping={},
        )