def __init__(self, group: ProcessGroup, device: int | str | torch.device) -> None:
        """
        Custom allreduce provides non-destructive acceleration and is
        available for CUDA and ROCm MI300 series.

        Custom quick allreduce leverages quantization for further
        acceleration on ROCm. It currently supports Q8, Q6, and Q4
        quantization formats and FP(float16, bfloat16).

        Quick allreduce is designed as a complement to custom allreduce.
        Its initialization requires even stricter conditions.

        Only the ROCm MI300 series is supported for quick allreduce at
        this time.

        Args:
            group: the process group to work on. If None, it will use the
                default process group.
            device: the device to bind the CustomAllreduce to. If None,
                it will be bound to f"cuda:{local_rank}".
        It is the caller's responsibility to make sure each communicator
        is bind to a unique device, and all communicators in this group
        are in the same node.
        """
        self.disabled = True
        if not self._rocm_arch_available():
            logger.debug(
                "Custom quick allreduce is only supported on ROCm MI300 series."
            )
            return

        if not quick_ar:
            # disable because of missing quick reduce library
            # e.g. in a cuda environment
            logger.info(
                "Custom quick allreduce is disabled because "
                "of missing custom quick allreduce library"
            )
            return

        self.group = group
        assert dist.get_backend(group) != dist.Backend.NCCL, (
            "Custom quick allreduce should be attached to a non-NCCL group."
        )
        if not all(in_the_same_node_as(group, source_rank=0)):
            # No need to initialize custom quick allreduce for
            # multi-node case.
            logger.warning(
                "Custom quick allreduce is disabled because this "
                "process group spans across nodes."
            )
            return
        rank = dist.get_rank(group=self.group)
        world_size = dist.get_world_size(group=self.group)
        self.rank = rank
        self.world_size = world_size
        if world_size == 1:
            # No need to initialize QuickReduce for single GPU case.
            return

        if world_size not in QuickAllReduce._SUPPORTED_WORLD_SIZES:
            logger.warning(
                "Custom quick allreduce is disabled due to an "
                "unsupported world size: %d. Supported world sizes: %s.",
                world_size,
                str(QuickAllReduce._SUPPORTED_WORLD_SIZES),
            )
            return

        if isinstance(device, int):
            device = torch.device(f"cuda:{device}")
        elif isinstance(device, str):
            device = torch.device(device)
        assert isinstance(device, torch.device)
        self.device = device

        cuda_visible_devices = envs.CUDA_VISIBLE_DEVICES
        if cuda_visible_devices:
            device_ids = list(map(int, cuda_visible_devices.split(",")))
        else:
            device_ids = list(range(current_platform.device_count()))
        physical_device_id = device_ids[device.index]
        tensor = torch.tensor([physical_device_id], dtype=torch.int, device="cpu")
        gather_list = [
            torch.tensor([0], dtype=torch.int, device="cpu")
            for _ in range(self.world_size)
        ]
        dist.all_gather(gather_list, tensor, group=self.group)
        physical_device_ids = [t.item() for t in gather_list]

        # test nvlink first, this will filter out most of the cases
        # where custom quick allreduce is not supported
        # this checks hardware and driver support for NVLink
        assert current_platform.is_cuda_alike()
        self.fully_connected = current_platform.is_fully_connected(physical_device_ids)
        if self.world_size > 2 and not self.fully_connected:
            logger.debug(
                "Custom quick allreduce is disabled because it's not supported "
                "on more than two PCIe-only GPUs. "
            )
            return

        self.init_quick_all_reduce()