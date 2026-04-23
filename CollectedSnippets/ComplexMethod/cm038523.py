def __init__(
        self,
        cpu_group: ProcessGroup,
        device: torch.device | None = None,
        device_group: ProcessGroup | None = None,
        unique_name: str = "",
        global_ranks: list[int] | None = None,
        global_world_size: int | None = None,
        tcp_store_group: StatelessProcessGroup | None = None,
    ):
        super().__init__(
            cpu_group,
            device,
            device_group,
            unique_name,
            global_ranks,
            global_world_size,
        )
        if "tp" not in unique_name:
            # custom allreduce or torch symm mem can be used only by tp
            use_custom_allreduce = False
            use_torch_symm_mem = False
            use_flashinfer_allreduce = False
        else:
            from vllm.distributed.parallel_state import _ENABLE_CUSTOM_ALL_REDUCE

            use_custom_allreduce = _ENABLE_CUSTOM_ALL_REDUCE
            use_torch_symm_mem = envs.VLLM_ALLREDUCE_USE_SYMM_MEM
            use_flashinfer_allreduce = envs.VLLM_ALLREDUCE_USE_FLASHINFER

        self.use_custom_allreduce = use_custom_allreduce
        self.use_torch_symm_mem = use_torch_symm_mem
        self.use_flashinfer_allreduce = use_flashinfer_allreduce

        # lazy import to avoid documentation build error
        from vllm.distributed.device_communicators.custom_all_reduce import (
            CustomAllreduce,
        )
        from vllm.distributed.device_communicators.flashinfer_all_reduce import (
            FlashInferAllReduce,
        )
        from vllm.distributed.device_communicators.pynccl import PyNcclCommunicator
        from vllm.distributed.device_communicators.quick_all_reduce import (
            QuickAllReduce,
        )
        from vllm.distributed.device_communicators.symm_mem import SymmMemCommunicator

        self.pynccl_comm: PyNcclCommunicator | None = None
        if self.world_size > 1:
            self.pynccl_comm = PyNcclCommunicator(
                group=self.cpu_group if tcp_store_group is None else tcp_store_group,
                device=self.device,
            )
            if is_symmetric_memory_enabled():
                register_nccl_symmetric_ops(self.pynccl_comm)

        self.ca_comm: CustomAllreduce | None = None
        self.qr_comm: QuickAllReduce | None = None
        self.symm_mem_comm: SymmMemCommunicator | None = None
        self.fi_ar_comm: FlashInferAllReduce | None = None

        if use_torch_symm_mem and current_platform.is_cuda():
            self.symm_mem_comm = SymmMemCommunicator(
                group=self.cpu_group,
                device=self.device,
            )

        if self.use_flashinfer_allreduce and self.world_size > 1:
            self.fi_ar_comm = FlashInferAllReduce(
                group=self.cpu_group,
                device=self.device,
            )

        if use_custom_allreduce and self.world_size > 1:
            # Initialize a custom fast all-reduce implementation.
            self.ca_comm = CustomAllreduce(
                group=self.cpu_group,
                device=self.device,
                symm_mem_enabled=(
                    self.symm_mem_comm is not None and not self.symm_mem_comm.disabled
                ),
            )

            if current_platform.is_rocm():
                # Initialize a custom quick all-reduce implementation for AMD.
                # Quick reduce is designed as a complement to custom allreduce.
                # Based on quickreduce (https://github.com/mk1-project/quickreduce).
                # If it's a rocm, 'use_custom_allreduce==True' means it must
                # currently be an MI300 series.
                self.qr_comm = QuickAllReduce(group=self.cpu_group, device=self.device)

        if self.use_all2all:
            if self.all2all_backend in ("naive", "allgather_reducescatter"):
                from .all2all import AgRsAll2AllManager

                self.all2all_manager = AgRsAll2AllManager(
                    self.cpu_group, tcp_store_group
                )
            elif self.all2all_backend == "deepep_high_throughput":
                from .all2all import DeepEPHTAll2AllManager

                self.all2all_manager = DeepEPHTAll2AllManager(
                    self.cpu_group, tcp_store_group
                )
            elif self.all2all_backend == "deepep_low_latency":
                from .all2all import DeepEPLLAll2AllManager

                self.all2all_manager = DeepEPLLAll2AllManager(
                    self.cpu_group, tcp_store_group
                )
            elif self.all2all_backend == "mori":
                from .all2all import MoriAll2AllManager

                self.all2all_manager = MoriAll2AllManager(self.cpu_group)
            elif self.all2all_backend == "nixl_ep":
                from .all2all import NixlEPAll2AllManager

                self.all2all_manager = NixlEPAll2AllManager(
                    self.cpu_group, tcp_store_group
                )
            elif (
                self.all2all_backend == "flashinfer_all2allv"
                or self.all2all_backend == "flashinfer_nvlink_two_sided"
            ):
                if self.all2all_backend == "flashinfer_all2allv":
                    logger.warning_once(
                        "'flashinfer_all2allv' is deprecated and has been renamed to"
                        "'flashinfer_nvlink_two_sided'. It will be removed in a future"
                        "release."
                    )
                from .all2all import FlashInferNVLinkTwoSidedManager

                self.all2all_manager = FlashInferNVLinkTwoSidedManager(
                    self.cpu_group, tcp_store_group
                )
            elif self.all2all_backend == "flashinfer_nvlink_one_sided":
                from .all2all import FlashInferNVLinkOneSidedManager

                self.all2all_manager = FlashInferNVLinkOneSidedManager(self.cpu_group)
            else:
                raise ValueError(f"Unknown all2all backend: {self.all2all_backend}")

            logger.info_once(
                "Using %s all2all manager.",
                self.all2all_manager.__class__.__name__,
                scope="global",
            )