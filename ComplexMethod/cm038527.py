def __init__(
        self,
        group: ProcessGroup,
        device: int | str | torch.device,
        # add options for testing
        force_multimem: bool | None = None,
        max_size_override: int | None = None,
    ):
        self.disabled = True

        if not symm_mem_available:
            return

        if not current_platform.is_cuda():
            logger.warning("SymmMemCommunicator: symmetric memory is not available.")
            return
        if isinstance(device, int):
            device = torch.device(f"cuda:{device}")
        elif isinstance(device, str):
            device = torch.device(device)
        torch.accelerator.set_device_index(device)
        self.dtype = torch.bfloat16
        self.device = device
        self.group = group
        self.world_size = dist.get_world_size(self.group)
        capability = current_platform.get_device_capability()
        if capability is None:
            logger.warning(
                "SymmMemCommunicator: device capability is unknown, "
                "communicator is not available."
            )
            return
        self.device_capability = capability.as_version_str()
        if self.device_capability not in SYMM_MEM_ALL_REDUCE_MAX_SIZES:
            logger.warning(
                "SymmMemCommunicator: Device capability %s not supported, "
                "communicator is not available.",
                self.device_capability,
            )
            return
        if self.world_size not in SYMM_MEM_ALL_REDUCE_MAX_SIZES[self.device_capability]:
            logger.warning(
                "SymmMemCommunicator: World size %d not supported, "
                "communicator is not available.",
                self.world_size,
            )
            return
        # Use override max_size if provided, otherwise use default
        if max_size_override is not None:
            self.max_size = max_size_override
            logger.info(
                "SymmMemCommunicator: Using override max_size: %s bytes",
                self.max_size,
            )
        else:
            self.max_size = SYMM_MEM_ALL_REDUCE_MAX_SIZES[self.device_capability][
                self.world_size
            ]
        try:
            self.buffer = torch_symm_mem.empty(
                self.max_size // self.dtype.itemsize,
                device=self.device,
                dtype=self.dtype,
            )
            handle = torch_symm_mem.rendezvous(self.buffer, self.group.group_name)
        except RuntimeError as e:
            logger.warning_once(
                "SymmMemCommunicator: symmetric memory initialization failed: %s "
                "Communicator is not available. To suppress this warning set "
                "VLLM_ALLREDUCE_USE_SYMM_MEM=0",
                str(e),
            )
            return
        if handle.multicast_ptr == 0:
            logger.warning(
                "SymmMemCommunicator: symmetric memory "
                "multicast operations are not supported."
            )
            return
        self.force_multimem = force_multimem
        self.disabled = False
        if envs.VLLM_BATCH_INVARIANT:
            self.disabled = True