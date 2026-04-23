def __init__(
        self,
        asyncio_mode: bool,
        vllm_config: VllmConfig,
        executor_class: type[Executor],
        log_stats: bool,
        client_addresses: dict[str, str] | None = None,
    ):
        self.vllm_config = vllm_config

        # ZMQ setup.
        sync_ctx = zmq.Context(io_threads=2)
        self.ctx = zmq.asyncio.Context(sync_ctx) if asyncio_mode else sync_ctx

        # This will ensure resources created so far are closed
        # when the client is garbage collected, even if an
        # exception is raised mid-construction.
        self.resources = BackgroundResources(ctx=sync_ctx)
        self._finalizer = weakref.finalize(self, self.resources)
        success = False
        try:
            # State used for data parallel.
            self.engines_running = False
            parallel_config = vllm_config.parallel_config
            # Elastic EP can remove a rank and later add it back with the same
            # identity. The client input ROUTER needs handover to allow the new
            # engine to replace the dead connection.
            enable_input_socket_handover = parallel_config.enable_elastic_ep

            self.stats_update_address: str | None = None
            tensor_queue: Queue | None = None
            if client_addresses:
                # Engines are managed externally to this client.
                input_address = client_addresses["input_address"]
                output_address = client_addresses["output_address"]
                self.stats_update_address = client_addresses.get("stats_update_address")
                # Tensor queues passed via client_addresses for multi-API-server case
                tensor_queue = client_addresses.get("tensor_queue")  # type: ignore[assignment]
                self.input_socket = self.resources.input_socket = make_zmq_socket(
                    self.ctx,
                    input_address,
                    zmq.ROUTER,
                    bind=True,
                    router_handover=enable_input_socket_handover,
                )
                self.resources.output_socket = make_zmq_socket(
                    self.ctx, output_address, zmq.PULL
                )
            else:
                # Engines are managed by this client.
                addresses = get_engine_zmq_addresses(vllm_config)
                self.input_socket = self.resources.input_socket = make_zmq_socket(
                    self.ctx,
                    addresses.inputs[0],
                    zmq.ROUTER,
                    bind=True,
                    router_handover=enable_input_socket_handover,
                )
                self.resources.output_socket = make_zmq_socket(
                    self.ctx, addresses.outputs[0], zmq.PULL
                )

                with launch_core_engines(
                    vllm_config, executor_class, log_stats, addresses
                ) as (engine_manager, coordinator, addresses, tensor_queue):
                    self.resources.coordinator = coordinator
                    self.resources.engine_manager = engine_manager

                self.stats_update_address = addresses.frontend_stats_publish_address
                if coordinator is not None:
                    assert self.stats_update_address == (
                        coordinator.get_stats_publish_address()
                    )

            # Serialization setup with tensor queues for multimodal tensor IPC.
            tensor_ipc_sender: TensorIpcSender | None = None
            model_config = getattr(vllm_config, "model_config", None)
            if model_config is not None and model_config.multimodal_config is not None:
                mm_tensor_ipc = model_config.multimodal_config.mm_tensor_ipc
                if mm_tensor_ipc == "torch_shm" and tensor_queue is not None:
                    tensor_ipc_sender = TensorIpcSender(tensor_queue)

            self.encoder = MsgpackEncoder(oob_tensor_consumer=tensor_ipc_sender)
            self.decoder = MsgpackDecoder(EngineCoreOutputs)

            dp_size = parallel_config.data_parallel_size
            dp_rank = parallel_config.data_parallel_index
            dp_local_size = parallel_config.data_parallel_size_local
            offline_mode = parallel_config.data_parallel_rank_local is not None
            # Client manages local+remote EngineCores in pure internal LB case.
            # Client manages local EngineCores in hybrid and external LB case.
            num_ranks = dp_local_size if parallel_config.local_engines_only else dp_size
            self.engine_ranks_managed = (
                [dp_rank] if offline_mode else list(range(dp_rank, dp_rank + num_ranks))
            )
            assert parallel_config.data_parallel_size_local <= len(
                self.engine_ranks_managed
            )

            # ZMQ identity of each engine that this client will talk to.
            self.core_engines: list[EngineIdentity] = [
                rank.to_bytes(2, "little") for rank in self.engine_ranks_managed
            ]

            # Wait for ready messages from each engine on the input socket.
            identities = set(self.core_engines)
            sync_input_socket = zmq.Socket.shadow(self.input_socket)
            while identities:
                if not sync_input_socket.poll(
                    timeout=VLLM_ENGINE_READY_TIMEOUT_S * 1000  # convert to ms
                ):
                    raise TimeoutError(
                        f"Timed out waiting for engine core processes to "
                        f"start. This is often caused by slow weight loading "
                        f"for large models. Waited "
                        f"{VLLM_ENGINE_READY_TIMEOUT_S}s (configured by "
                        f"VLLM_ENGINE_READY_TIMEOUT_S). To increase the "
                        f"timeout, set the environment variable: "
                        f"VLLM_ENGINE_READY_TIMEOUT_S=<seconds>"
                    )
                identity, payload = sync_input_socket.recv_multipart()
                identities.remove(identity)
                self._apply_ready_response(payload)

            self.core_engine: EngineIdentity = self.core_engines[0]
            self.utility_results: dict[int, AnyFuture] = {}

            # Request objects which may contain pytorch-allocated tensors
            # that we need to keep references to until zmq is done with the
            # underlying data.
            self.pending_messages = deque[tuple[zmq.MessageTracker, Any]]()

            # Start monitoring engine core processes for unexpected failures
            self.start_engine_core_monitor()

            success = True
        finally:
            if not success:
                self._finalizer()