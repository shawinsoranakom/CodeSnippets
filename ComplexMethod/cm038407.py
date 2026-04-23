def __init__(
        self,
        group_ranks: list[list[int]],
        local_rank: int,
        torch_distributed_backend: str | Backend,
        use_device_communicator: bool,
        coord_store: Store,
        use_message_queue_broadcaster: bool = False,
        group_name: str | None = None,
        host: str = "127.0.0.1",
        global_rank: int = 0,
        global_world_size: int = 1,
    ):
        group_name = group_name or "anonymous"
        self.unique_name = _get_unique_name(group_name)
        _register_group(self)

        self.rank = global_rank
        self.local_rank = local_rank

        self_device_group = None
        self_cpu_group = None
        self_tcp_store_group = None

        from vllm.platforms import current_platform

        backend = str(torch_distributed_backend)
        self.backend = backend
        for idx, ranks in enumerate(group_ranks):
            if self.rank in ranks:
                self.ranks = ranks
                self.world_size = len(ranks)
                self.rank_in_group = ranks.index(self.rank)

                key = f"{group_name}_{idx}"
                if self.rank_in_group == 0:
                    ports, socks = _allocate_group_ports(
                        key,
                        host,
                        coord_store,
                    )
                else:
                    ports = _fetch_group_ports(key, coord_store)
                    socks = []
                device_port, cpu_port, tcp_store_port = ports

                device_group = stateless_init_torch_distributed_process_group(
                    host=host,
                    port=device_port,
                    rank=self.rank_in_group,
                    world_size=self.world_size,
                    backend=backend,
                    group_name=f"{self.unique_name}_device",
                    listen_socket=socks[0] if socks else None,
                )
                cpu_group = stateless_init_torch_distributed_process_group(
                    host=host,
                    port=cpu_port,
                    rank=self.rank_in_group,
                    world_size=self.world_size,
                    backend="gloo",
                    group_name=f"{self.unique_name}_cpu",
                    listen_socket=socks[1] if socks else None,
                )
                tcp_store_group = StatelessProcessGroup.create(
                    host=host,
                    port=tcp_store_port,
                    rank=self.rank_in_group,
                    world_size=self.world_size,
                    listen_socket=socks[2] if socks else None,
                )

                self_device_group = device_group
                self_cpu_group = cpu_group
                self_tcp_store_group = tcp_store_group

        assert self_cpu_group is not None
        assert self_device_group is not None
        assert self_tcp_store_group is not None

        self.cpu_group = self_cpu_group
        self.device_group = self_device_group
        self.tcp_store_group = self_tcp_store_group

        if current_platform.is_cuda_alike():
            self.device = torch.device(f"cuda:{local_rank}")
        elif current_platform.is_xpu():
            self.device = torch.device(f"xpu:{local_rank}")
        elif current_platform.is_out_of_tree():
            self.device = torch.device(f"{current_platform.device_name}:{local_rank}")
        else:
            self.device = torch.device("cpu")

        self.use_device_communicator = use_device_communicator
        self.device_communicator = None
        if use_device_communicator and self.world_size > 1:
            device_comm_cls = resolve_obj_by_qualname(
                current_platform.get_device_communicator_cls()
            )
            assert device_comm_cls == CudaCommunicator
            self.device_communicator = CudaCommunicator(
                cpu_group=self.cpu_group,
                device=self.device,
                device_group=self.device_group,
                unique_name=self.unique_name,
                global_ranks=self.ranks,
                global_world_size=global_world_size,
                tcp_store_group=self.tcp_store_group,
            )

        self.mq_broadcaster = None

        self.use_custom_op_call = (
            current_platform.is_cuda_alike() or current_platform.is_tpu()
        )
        self.use_cpu_custom_send_recv = False