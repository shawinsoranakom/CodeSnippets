def __init__(
        self,
        cpu_group: ProcessGroup,
        device: torch.device | None = None,
        device_group: ProcessGroup | None = None,
        unique_name: str = "",
    ):
        super().__init__(cpu_group, device, device_group, unique_name)
        self.dist_module = torch.distributed

        if (
            (
                current_platform.get_cpu_architecture() == CpuArchEnum.X86
                or current_platform.get_cpu_architecture() == CpuArchEnum.ARM
            )
            and hasattr(torch.ops._C, "init_shm_manager")
            and (unique_name.startswith("tp") or unique_name.startswith("pp"))
            and self._all_group_ranks_share_shm_group_name()
        ):
            self.dist_module = _CPUSHMDistributed(self)
        elif unique_name.startswith("tp") or unique_name.startswith("pp"):
            logger.info(
                "CPU SHM communicator disabled for group %s: ranks do not share "
                "the same SHM group name, falling back to torch.distributed.",
                unique_name,
            )

        # send/recv tensor_dict is only supported through the SHM communicator backend
        self.supports_tensor_dict = isinstance(self.dist_module, _CPUSHMDistributed)

        if self.use_all2all:
            if self.all2all_backend not in (
                "naive",
                "allgather_reducescatter",
            ):  # type: ignore[has-type]
                logger.warning(
                    "`%s` all2all manager is not supported on CPU. "
                    "Falling back to `allgather_reducescatter` manager.",
                    self.all2all_backend,  # type: ignore[has-type]
                )
            from .all2all import AgRsAll2AllManager

            self.all2all_manager = AgRsAll2AllManager(self.cpu_group)
            logger.info("Using allgather_reducescatter all2all manager.")