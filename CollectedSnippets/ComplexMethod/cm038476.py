def __init__(
        self,
        local_rank: int,
        config: KVTransferConfig,
        hostname: str = "",
        port_offset: int = 0,
        library_path: str | None = None,
    ) -> None:
        self.config = config
        self.rank = port_offset
        self.local_rank = local_rank
        self.device = torch.device(f"cuda:{self.local_rank}")
        self.nccl = NCCLLibrary(library_path)

        if not hostname:
            hostname = get_ip()
        port = int(self.config.kv_port) + port_offset
        if port == 0:
            raise ValueError("Port cannot be 0")
        self._hostname = hostname
        self._port = port

        # Each card corresponds to a ZMQ address.
        self.zmq_address = f"{self._hostname}:{self._port}"

        # If `proxy_ip` or `proxy_port` is `""`,
        # then the ping thread will not be enabled.
        proxy_ip = self.config.get_from_extra_config("proxy_ip", "")
        proxy_port = self.config.get_from_extra_config("proxy_port", "")
        if proxy_ip == "" or proxy_port == "":
            self.proxy_address = ""
            self.http_address = ""
        else:
            self.proxy_address = proxy_ip + ":" + proxy_port
            # the `http_port` must be consistent with the port of OpenAI.
            http_port = self.config.get_from_extra_config("http_port", None)
            if http_port is None:
                example_cfg = {
                    "kv_connector": "P2pNcclConnector",
                    "kv_connector_extra_config": {"http_port": 8000},
                }
                example = (
                    f"--port=8000 --kv-transfer-config='{json.dumps(example_cfg)}'"
                )
                raise ValueError(
                    "kv_connector_extra_config.http_port is required. "
                    f"Example: {example}"
                )
            self.http_address = f"{self._hostname}:{http_port}"

        self.context = zmq.Context()
        self.router_socket = self.context.socket(zmq.ROUTER)
        self.router_socket.bind(f"tcp://{self.zmq_address}")

        self.poller = zmq.Poller()
        self.poller.register(self.router_socket, zmq.POLLIN)

        self.send_store_cv = threading.Condition()
        self.send_queue_cv = threading.Condition()
        self.recv_store_cv = threading.Condition()

        self.send_stream = torch.cuda.Stream()
        self.recv_stream = torch.cuda.Stream()

        mem_pool_size_gb = float(
            self.config.get_from_extra_config(
                "mem_pool_size_gb", DEFAULT_MEM_POOL_SIZE_GB
            )
        )
        self.pool = TensorMemoryPool(
            max_block_size=int(mem_pool_size_gb * 1024**3)
        )  # GB

        # The sending type includes tree mutually exclusive options:
        # PUT, GET, PUT_ASYNC.
        self.send_type = self.config.get_from_extra_config("send_type", "PUT_ASYNC")
        if self.send_type == "GET":
            # tensor_id: torch.Tensor
            self.send_store: dict[str, torch.Tensor] = {}
        else:
            # PUT or PUT_ASYNC
            # tensor_id: torch.Tensor
            self.send_queue: deque[SendQueueItem] = deque()
            if self.send_type == "PUT_ASYNC":
                self._send_thread = threading.Thread(
                    target=self.send_async, daemon=True
                )
                self._send_thread.start()

        # tensor_id: torch.Tensor/(addr, dtype, shape)
        self.recv_store: dict[str, Any] = {}
        self.recv_request_id_to_tensor_ids: dict[str, set[str]] = {}
        self.send_request_id_to_tensor_ids: dict[str, set[str]] = {}
        self.socks: dict[str, Any] = {}  # remote_address: client socket
        self.comms: dict[str, Any] = {}  # remote_address: (ncclComm_t, rank)

        self.buffer_size = 0
        self.buffer_size_threshold = float(self.config.kv_buffer_size)

        self.nccl_num_channels = self.config.get_from_extra_config(
            "nccl_num_channels", "8"
        )

        self._listener_thread = threading.Thread(
            target=self.listen_for_requests, daemon=True
        )
        self._listener_thread.start()

        self._ping_thread = None
        if port_offset == 0 and self.proxy_address != "":
            self._ping_thread = threading.Thread(target=self.ping, daemon=True)
            self._ping_thread.start()

        logger.info(
            "💯P2pNcclEngine init, rank:%d, local_rank:%d, http_address:%s, "
            "zmq_address:%s, proxy_address:%s, send_type:%s, buffer_size_"
            "threshold:%.2f, nccl_num_channels:%s",
            self.rank,
            self.local_rank,
            self.http_address,
            self.zmq_address,
            self.proxy_address,
            self.send_type,
            self.buffer_size_threshold,
            self.nccl_num_channels,
        )