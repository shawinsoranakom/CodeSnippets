def init_pg(self, eager_init, backend: str | None = None) -> None:
        if backend is None:
            backend = self.backend

        requires_gpu = any(
            gpu_backend in backend for gpu_backend in ACCELERATOR_DIST_BACKENDS
        )
        if requires_gpu and torch.accelerator.device_count() < self.world_size:
            sys.exit(TEST_SKIPS[f"multi-gpu-{self.world_size}"].exit_code)

        curr_backend = dist.get_default_backend_for_device(self.device_type)

        if backend not in [
            "nccl",
            "gloo",
            "mpi",
            f"cpu:gloo,{self.device_type}:{curr_backend}",
            "cpu:gloo,cuda:ncclx",
            "cuda:ncclx",
            "hccl",
            "xccl",
            "fake",
            "cpu:gloo,xpu:xccl",
        ]:
            raise RuntimeError(f"Backend {backend} not supported!")

        device_id = None
        if "nccl" in backend or "xccl" in backend:
            # set device for nccl pg for collectives
            # TODO: if users want to enable testing across hosts, we may need
            # to change this part.
            torch.accelerator.set_device_index(self.rank)
            # we only need to set device_id for nccl backend with eager init
            device_id = (
                torch.device(f"{self.device_type}:{self.rank}") if eager_init else None
            )

        # For nccl backend, bind the device to the process if device_id is not None
        # so the nccl communicator is immediately formed and we can use `ncclCommSplit`
        # for form subgroup to avoid unnecessary overhead.
        dist.init_process_group(
            backend=backend,
            world_size=self.world_size,
            rank=self.rank,  # pyre-ignore[16]
            init_method=f"file://{self.file_name}",  # pyre-ignore[16]
            device_id=device_id,
        )