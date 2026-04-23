def __init__(
        self,
        cpu_group: ProcessGroup,
        expert_weights: Sequence[torch.Tensor],
        cuda_stream: torch.cuda.Stream | None = None,
    ) -> None:
        assert expert_weights, "NixlEplbCommunicator requires non-empty expert_weights."
        if NixlWrapper is None:
            raise RuntimeError("NIXL/ RIXL is unavailable.")
        self._cpu_group = cpu_group
        self._cuda_stream = cuda_stream
        self._world_size = cpu_group.size()
        self._rank = cpu_group.rank()
        self._send_tensors: dict[torch.dtype, list[list[torch.Tensor]]] = {}
        self._recv_tensors: dict[torch.dtype, list[list[torch.Tensor]]] = {}
        self._dtypes: list[torch.dtype] = []
        self._device = expert_weights[0].device
        for tensor in expert_weights:
            assert tensor.device == self._device, (
                "All local EPLB tensors are expected to be on the same device: "
                f"expected={self._device}, got={tensor.device}"
            )
            if tensor.dtype not in self._dtypes:
                self._dtypes.append(tensor.dtype)

        config = (
            nixl_agent_config(capture_telemetry=False)
            if nixl_agent_config is not None
            else None
        )
        self._nixl_wrapper = NixlWrapper(self._make_agent_name(), config)
        self._nixl_memory_type = "VRAM"
        self._registered_desc: object | None = None
        self._remote_agents: dict[int, str] = {}
        self._remote_send_meta: dict[int, tuple[int, int, int]] = {}
        self._send_buffer: torch.Tensor = torch.empty(0)
        self._recv_buffer: torch.Tensor = torch.empty(0)
        self._peer_partition_bytes: int = 0
        self._dtype_max_bytes: dict[torch.dtype, int] = {}
        self._cuda_device_id = int(self._device.index or 0)
        self._xfer_cache: dict[tuple[int, int, int], tuple[int, int, int]] = {}
        self._init_step("buffers", self._init_registered_buffers, expert_weights)
        self._init_step("agents", self._init_remote_agents)
        self._init_step("send meta", self._exchange_remote_send_meta)
        self._log_initialized()